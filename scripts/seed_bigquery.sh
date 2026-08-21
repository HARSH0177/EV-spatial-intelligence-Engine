#!/bin/bash
# ============================================================
# BigQuery seed script — production schema v2.1
# New in v2.1: station_registry table (Improvement 1)
# Usage: bash scripts/seed_bigquery.sh YOUR_PROJECT_ID
# ============================================================
set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
DATASET="mcp_mobility"

echo ">>> Using project: $PROJECT_ID"

bq --project_id=$PROJECT_ID mk \
  --dataset --location=US --description="EV Mobility MCP Dataset v2.1" \
  $PROJECT_ID:$DATASET 2>/dev/null || echo "Dataset exists"

# ── station_registry (NEW — Improvement 1) ───────────────────────────────────
echo ">>> Creating station_registry table..."
bq --project_id=$PROJECT_ID mk --table \
  $DATASET.station_registry \
  "station_id:STRING,name:STRING,lat:FLOAT,lon:FLOAT,city:STRING,zip_code:STRING,network:STRING,kw:INTEGER,total_ports:INTEGER,connector_types:STRING,data_source:STRING,is_active:BOOL" \
  2>/dev/null || echo "station_registry exists"

cat > /tmp/station_registry.json << 'JSON'
{"station_id":"ST001","name":"Mission District Fast Charge","lat":37.7599,"lon":-122.4148,"city":"San Francisco","zip_code":"94102","network":"EVgo","kw":150,"total_ports":8,"connector_types":"CCS,CHAdeMO","data_source":"ocpp_live","is_active":true}
{"station_id":"ST002","name":"SoMa SuperCharge Hub","lat":37.7785,"lon":-122.4058,"city":"San Francisco","zip_code":"94103","network":"Tesla","kw":250,"total_ports":12,"connector_types":"Tesla","data_source":"ocpp_live","is_active":true}
{"station_id":"ST003","name":"Civic Center ChargePoint","lat":37.7793,"lon":-122.4177,"city":"San Francisco","zip_code":"94102","network":"ChargePoint","kw":22,"total_ports":6,"connector_types":"J1772","data_source":"ocpp_live","is_active":true}
{"station_id":"ST004","name":"Castro EV Hub","lat":37.7609,"lon":-122.4350,"city":"San Francisco","zip_code":"94114","network":"ChargePoint","kw":100,"total_ports":4,"connector_types":"CCS,CHAdeMO","data_source":"ocpp_live","is_active":true}
{"station_id":"ST005","name":"Dogpatch Rapid Charge","lat":37.7576,"lon":-122.3934,"city":"San Francisco","zip_code":"94107","network":"EVgo","kw":150,"total_ports":6,"connector_types":"CCS,CHAdeMO","data_source":"ocpp_live","is_active":true}
{"station_id":"ST006","name":"Potrero Hill Charger","lat":37.7638,"lon":-122.4058,"city":"San Francisco","zip_code":"94114","network":"Blink","kw":22,"total_ports":3,"connector_types":"J1772","data_source":"ocpp_live","is_active":true}
JSON
bq --project_id=$PROJECT_ID load --source_format=NEWLINE_DELIMITED_JSON \
  $DATASET.station_registry /tmp/station_registry.json

# ── charger_events ────────────────────────────────────────────────────────────
bq --project_id=$PROJECT_ID mk --table \
  --time_partitioning_field=timestamp --time_partitioning_type=DAY \
  $DATASET.charger_events \
  "event_id:STRING,station_id:STRING,port_id:STRING,event_type:STRING,status:STRING,error_code:STRING,timestamp:TIMESTAMP" \
  2>/dev/null || echo "charger_events exists"

# ── port_status ───────────────────────────────────────────────────────────────
bq --project_id=$PROJECT_ID mk --table \
  $DATASET.port_status \
  "station_id:STRING,port_id:STRING,status:STRING,last_updated:TIMESTAMP,session_id:STRING,session_start:TIMESTAMP" \
  2>/dev/null || echo "port_status exists"

# ── session_history ───────────────────────────────────────────────────────────
bq --project_id=$PROJECT_ID mk --table \
  --time_partitioning_field=start_time --time_partitioning_type=DAY \
  $DATASET.session_history \
  "session_id:STRING,station_id:STRING,port_id:STRING,start_time:TIMESTAMP,end_time:TIMESTAMP,energy_kwh:FLOAT,duration_minutes:INTEGER" \
  2>/dev/null || echo "session_history exists"

# ── zone_profile ──────────────────────────────────────────────────────────────
bq --project_id=$PROJECT_ID mk --table $DATASET.zone_profile \
  "city:STRING,zip_code:STRING,population:INTEGER,ev_registrations:INTEGER,median_income:INTEGER,avg_daily_traffic:INTEGER,grid_capacity_kw:INTEGER,land_cost_index:FLOAT,accessibility_score:FLOAT" \
  2>/dev/null || true
cat > /tmp/zone_profile.json << 'JSON'
{"city":"San Francisco","zip_code":"94102","population":42000,"ev_registrations":1850,"median_income":95000,"avg_daily_traffic":38000,"grid_capacity_kw":4200,"land_cost_index":0.72,"accessibility_score":0.88}
{"city":"San Francisco","zip_code":"94103","population":37500,"ev_registrations":2100,"median_income":112000,"avg_daily_traffic":52000,"grid_capacity_kw":5800,"land_cost_index":0.65,"accessibility_score":0.92}
{"city":"San Francisco","zip_code":"94110","population":61000,"ev_registrations":980,"median_income":68000,"avg_daily_traffic":29000,"grid_capacity_kw":3100,"land_cost_index":0.41,"accessibility_score":0.75}
{"city":"San Francisco","zip_code":"94107","population":28000,"ev_registrations":3200,"median_income":145000,"avg_daily_traffic":61000,"grid_capacity_kw":6500,"land_cost_index":0.58,"accessibility_score":0.95}
{"city":"San Francisco","zip_code":"94114","population":33000,"ev_registrations":1600,"median_income":88000,"avg_daily_traffic":21000,"grid_capacity_kw":2800,"land_cost_index":0.35,"accessibility_score":0.70}
JSON
bq --project_id=$PROJECT_ID load --source_format=NEWLINE_DELIMITED_JSON \
  $DATASET.zone_profile /tmp/zone_profile.json

# ── competition_index ─────────────────────────────────────────────────────────
bq --project_id=$PROJECT_ID mk --table $DATASET.competition_index \
  "city:STRING,zip_code:STRING,competitor_name:STRING,station_count:INTEGER,avg_charger_kw:INTEGER,avg_monthly_sessions:INTEGER,market_share_pct:FLOAT" \
  2>/dev/null || true
cat > /tmp/competition_index.json << 'JSON'
{"city":"San Francisco","zip_code":"94102","competitor_name":"ChargePoint","station_count":3,"avg_charger_kw":50,"avg_monthly_sessions":420,"market_share_pct":0.28}
{"city":"San Francisco","zip_code":"94103","competitor_name":"EVgo","station_count":5,"avg_charger_kw":150,"avg_monthly_sessions":910,"market_share_pct":0.45}
{"city":"San Francisco","zip_code":"94110","competitor_name":null,"station_count":0,"avg_charger_kw":0,"avg_monthly_sessions":0,"market_share_pct":0.0}
{"city":"San Francisco","zip_code":"94107","competitor_name":"Tesla Supercharger","station_count":2,"avg_charger_kw":250,"avg_monthly_sessions":1200,"market_share_pct":0.38}
{"city":"San Francisco","zip_code":"94114","competitor_name":null,"station_count":1,"avg_charger_kw":22,"avg_monthly_sessions":110,"market_share_pct":0.09}
JSON
bq --project_id=$PROJECT_ID load --source_format=NEWLINE_DELIMITED_JSON \
  $DATASET.competition_index /tmp/competition_index.json

# ── charger_usage ─────────────────────────────────────────────────────────────
bq --project_id=$PROJECT_ID mk --table $DATASET.charger_usage \
  "city:STRING,zip_code:STRING,avg_session_kwh:FLOAT,avg_session_minutes:INTEGER,peak_hour:INTEGER,utilization_rate:FLOAT,sessions_per_day:INTEGER" \
  2>/dev/null || true
cat > /tmp/charger_usage.json << 'JSON'
{"city":"San Francisco","zip_code":"94102","avg_session_kwh":32.4,"avg_session_minutes":28,"peak_hour":8,"utilization_rate":0.61,"sessions_per_day":18}
{"city":"San Francisco","zip_code":"94103","avg_session_kwh":48.1,"avg_session_minutes":22,"peak_hour":9,"utilization_rate":0.79,"sessions_per_day":31}
{"city":"San Francisco","zip_code":"94110","avg_session_kwh":28.0,"avg_session_minutes":35,"peak_hour":18,"utilization_rate":0.38,"sessions_per_day":9}
{"city":"San Francisco","zip_code":"94107","avg_session_kwh":58.7,"avg_session_minutes":19,"peak_hour":8,"utilization_rate":0.87,"sessions_per_day":44}
{"city":"San Francisco","zip_code":"94114","avg_session_kwh":24.3,"avg_session_minutes":41,"peak_hour":17,"utilization_rate":0.29,"sessions_per_day":6}
JSON
bq --project_id=$PROJECT_ID load --source_format=NEWLINE_DELIMITED_JSON \
  $DATASET.charger_usage /tmp/charger_usage.json

# ── recommendations ───────────────────────────────────────────────────────────
bq --project_id=$PROJECT_ID mk --table $DATASET.recommendations \
  "recommendation_id:STRING,city:STRING,created_at:TIMESTAMP,top_zip_codes:STRING,report_summary:STRING,agent_version:STRING" \
  2>/dev/null || true

echo ""
echo "============================================="
echo " BigQuery v2.1 setup complete: $PROJECT_ID.$DATASET"
echo " Tables: station_registry (NEW), charger_events, port_status,"
echo "         session_history, zone_profile, competition_index,"
echo "         charger_usage, recommendations"
echo "============================================="
