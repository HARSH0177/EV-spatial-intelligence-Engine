#!/bin/bash
# ============================================================
# Cloud Run Deploy Script — EV Advisor v2.2.1
#
# v2.2.1 fixes
# ------------
# BUG 6 FIXED: init_bigquery.py is inside scripts/ — path was correct,
#   but now made explicit with $SCRIPT_DIR for safety.
# BUG 7 FIXED: DEPLOY_REGION now defaults to us-central1 to match
#   BigQuery default location US. Set DEPLOY_REGION env var to
#   override if you need a different region.
#   If your BQ dataset is in EU, set:
#     DEPLOY_REGION=europe-west1 BIGQUERY_LOCATION=EU bash scripts/deploy.sh
#
# Usage:
#   bash scripts/deploy.sh YOUR_PROJECT_ID [--no-simulator]
# ============================================================
set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
SKIP_SIM=${2:-""}

# BUG 7 FIX: default region matches BigQuery US location
REGION="${DEPLOY_REGION:-us-central1}"
BQ_LOCATION="${BIGQUERY_LOCATION:-US}"
DATASET="${BIGQUERY_DATASET:-ev_advisor_core}"
IMAGE="gcr.io/$PROJECT_ID/ev-advisor:latest"

# BUG 6 FIX: resolve script directory so path is always correct
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================="
echo " EV Advisor Deploy v2.2.1"
echo " Project    : $PROJECT_ID"
echo " Region     : $REGION"
echo " BQ Location: $BQ_LOCATION"
echo " Dataset    : $DATASET"
echo "============================================="

# ── 1. Enable APIs ────────────────────────────────────────────────────────────
echo ""
echo ">>> [1/7] Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  bigquery.googleapis.com \
  containerregistry.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  --project=$PROJECT_ID --quiet

# ── 2. Bootstrap BigQuery ─────────────────────────────────────────────────────
echo ""
echo ">>> [2/7] Bootstrapping BigQuery dataset $DATASET (location=$BQ_LOCATION)..."
# BUG 6 FIX: use absolute path resolved from script location
python "$SCRIPT_DIR/init_bigquery.py" \
  --project "$PROJECT_ID" \
  --dataset "$DATASET" \
  --location "$BQ_LOCATION" \
  || echo "    (BQ bootstrap skipped — run manually if this is first deploy)"

# ── 3. Store secrets in Secret Manager ───────────────────────────────────────
echo ""
echo ">>> [3/7] Storing API keys in Secret Manager..."
if [ -n "$OPENCHARGEMAP_API_KEY" ]; then
  printf '%s' "$OPENCHARGEMAP_API_KEY" | \
    gcloud secrets create ocm-api-key --data-file=- --project=$PROJECT_ID 2>/dev/null || \
  printf '%s' "$OPENCHARGEMAP_API_KEY" | \
    gcloud secrets versions add ocm-api-key --data-file=- --project=$PROJECT_ID
  echo "    OCM API key stored"
else
  echo "    OPENCHARGEMAP_API_KEY not set — using rate-limited free access"
fi

if [ -n "$GOOGLE_MAPS_API_KEY" ]; then
  printf '%s' "$GOOGLE_MAPS_API_KEY" | \
    gcloud secrets create google-maps-key --data-file=- --project=$PROJECT_ID 2>/dev/null || \
  printf '%s' "$GOOGLE_MAPS_API_KEY" | \
    gcloud secrets versions add google-maps-key --data-file=- --project=$PROJECT_ID
  echo "    Google Maps key stored"
fi

# ── 4. Build Docker image ─────────────────────────────────────────────────────
echo ""
echo ">>> [4/7] Building Docker image..."
cd "$PROJECT_ROOT"
gcloud builds submit --tag "$IMAGE" --project=$PROJECT_ID .

# ── 5. Deploy OCPP Central ───────────────────────────────────────────────────
echo ""
echo ">>> [5/7] Deploying OCPP Central System..."
gcloud run deploy ev-ocpp-central \
  --image "$IMAGE" \
  --command "python,-m,realtime.ocpp_central" \
  --platform managed \
  --region "$REGION" \
  --no-allow-unauthenticated \
  --set-env-vars "\
GOOGLE_CLOUD_PROJECT=$PROJECT_ID,\
BIGQUERY_DATASET=$DATASET,\
OCPP_PORT=9000,\
LOG_LEVEL=INFO" \
  --memory 512Mi --cpu 1 \
  --min-instances 1 --max-instances 3 \
  --port 9000 \
  --project=$PROJECT_ID

OCPP_URL=$(gcloud run services describe ev-ocpp-central \
  --region="$REGION" \
  --format='value(status.url)' \
  --project=$PROJECT_ID)
OCPP_WS_URL="${OCPP_URL/https:\/\//wss://}"
echo "    OCPP Central: $OCPP_WS_URL"

# ── 6. Deploy FastAPI app ─────────────────────────────────────────────────────
echo ""
echo ">>> [6/7] Deploying FastAPI application..."
gcloud run deploy ev-advisor-api \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "\
GOOGLE_CLOUD_PROJECT=$PROJECT_ID,\
BIGQUERY_DATASET=$DATASET,\
BIGQUERY_LOCATION=$BQ_LOCATION,\
OCPP_WS_URL=$OCPP_WS_URL,\
LLM_ENABLED=true,\
ENABLE_OCM=true,\
ENABLE_OSM_OVERPASS=true,\
ENABLE_GOOGLE_PLACES=false,\
GEO_CACHE_TTL_SECONDS=86400,\
PROVIDER_CACHE_TTL_SECONDS=900,\
ADVISOR_CACHE_TTL_SECONDS=3600,\
DEFAULT_SEARCH_RADIUS_KM=10,\
LOG_LEVEL=INFO" \
  --memory 1Gi --cpu 2 \
  --min-instances 0 --max-instances 10 \
  --port 8080 \
  --project=$PROJECT_ID

API_URL=$(gcloud run services describe ev-advisor-api \
  --region="$REGION" \
  --format='value(status.url)' \
  --project=$PROJECT_ID)

# Grant IAM roles to service account
SA=$(gcloud run services describe ev-advisor-api \
  --region="$REGION" \
  --format='value(spec.template.spec.serviceAccountName)' \
  --project=$PROJECT_ID 2>/dev/null || echo "")

if [ -n "$SA" ]; then
  echo "    Granting Vertex AI + Secret Manager roles to $SA..."
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA" \
    --role="roles/aiplatform.user" --quiet
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA" \
    --role="roles/secretmanager.secretAccessor" --quiet 2>/dev/null || true
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA" \
    --role="roles/bigquery.dataEditor" --quiet 2>/dev/null || true
fi

# ── 7. Deploy Simulator (optional) ───────────────────────────────────────────
if [ "$SKIP_SIM" != "--no-simulator" ]; then
  echo ""
  echo ">>> [7/7] Deploying OCPP Simulator (demo/dev mode)..."
  gcloud run deploy ev-ocpp-simulator \
    --image "$IMAGE" \
    --command "python,-m,realtime.ocpp_simulator" \
    --platform managed \
    --region "$REGION" \
    --no-allow-unauthenticated \
    --set-env-vars "\
GOOGLE_CLOUD_PROJECT=$PROJECT_ID,\
BIGQUERY_DATASET=$DATASET,\
OCPP_WS_URL=$OCPP_WS_URL,\
OCPP_SIMULATE_STATIONS=ST001,ST002,ST003,ST004,ST005,ST006,\
LOG_LEVEL=INFO" \
    --memory 512Mi --cpu 1 \
    --min-instances 1 --max-instances 1 \
    --port 8080 \
    --project=$PROJECT_ID
  echo "    Simulator deployed"
else
  echo ">>> [7/7] Skipping simulator (--no-simulator)"
fi

# ── Smoke tests ───────────────────────────────────────────────────────────────
echo ""
echo ">>> Running smoke tests..."
sleep 5

check() {
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$1")
  if [ "$CODE" = "200" ]; then
    echo "    ✓ $2 → $CODE"
  else
    echo "    ✗ $2 → $CODE (check logs)"
  fi
}

check "$API_URL/health" "/health"
check "$API_URL/ready"  "/ready"

curl -s -o /dev/null -w "    %{http_code}" -X POST "$API_URL/api/search/chargers" \
  -H "Content-Type: application/json" \
  -d '{"location":"San Francisco, CA","max_distance_km":5}' && \
  echo "  /api/search/chargers"

curl -s -o /dev/null -w "    %{http_code}" -X POST "$API_URL/api/advisor/analyze-area" \
  -H "Content-Type: application/json" \
  -d '{"location":"Pune, India","top_n":3}' && \
  echo "  /api/advisor/analyze-area"

echo ""
echo "============================================="
echo " DEPLOYMENT COMPLETE v2.2.1"
echo ""
echo " API URL  : $API_URL"
echo " Frontend : $API_URL/app"
echo " API Docs : $API_URL/docs"
echo " OCPP WS  : $OCPP_WS_URL"
echo ""
echo " Rollback:"
echo "   gcloud run services update-traffic ev-advisor-api \\"
echo "     --to-revisions=PREVIOUS=100 --region=$REGION"
echo "============================================="