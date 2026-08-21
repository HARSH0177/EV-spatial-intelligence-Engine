@echo off
REM ============================================================
REM EV Advisor — Project Structure Setup Script
REM Run this ONCE from inside the "ev advisor new live" folder.
REM It creates all subdirectories and moves every file to the
REM correct location so the project can be imported and run.
REM ============================================================

echo.
echo === EV Advisor Project Setup ===
echo.

REM ── Create all package directories ───────────────────────────
echo [1/8] Creating directories...
mkdir agents       2>nul
mkdir api          2>nul
mkdir frontend     2>nul
mkdir llm          2>nul
mkdir middleware   2>nul
mkdir models       2>nul
mkdir realtime     2>nul
mkdir scripts      2>nul
mkdir tests        2>nul
mkdir utils        2>nul
mkdir .github\workflows 2>nul
echo     Done.

REM ── agents/ ───────────────────────────────────────────────────
echo [2/8] Moving agents...
move /Y "advisor_agent.py"   "agents\advisor_agent.py"   >nul 2>&1
move /Y "data_agent.py"      "agents\data_agent.py"      >nul 2>&1
move /Y "driver_agent.py"    "agents\driver_agent.py"    >nul 2>&1
move /Y "explanation_agent.py" "agents\explanation_agent.py" >nul 2>&1
move /Y "orchestrator.py"    "agents\orchestrator.py"    >nul 2>&1
move /Y "scoring_agent.py"   "agents\scoring_agent.py"   >nul 2>&1

REM ── api/ ──────────────────────────────────────────────────────
echo [3/8] Moving api...
move /Y "main.py"            "api\main.py"               >nul 2>&1
move /Y "routes_advisor.py"  "api\routes_advisor.py"     >nul 2>&1
move /Y "routes_discover.py" "api\routes_discover.py"    >nul 2>&1
move /Y "schemas.py"         "api\schemas.py"            >nul 2>&1

REM ── frontend/ ─────────────────────────────────────────────────
echo [4/8] Moving frontend...
move /Y "index.html"     "frontend\index.html"       >nul 2>&1
move /Y "index (2).html" "frontend\index.html"       >nul 2>&1
move /Y "index (2)"      "frontend\index.html"       >nul 2>&1

REM ── llm/ ──────────────────────────────────────────────────────
echo [5/8] Moving llm...
move /Y "vertex_explainer.py" "llm\vertex_explainer.py" >nul 2>&1

REM ── middleware/ ───────────────────────────────────────────────
echo [6/8] Moving middleware...
move /Y "auth.py" "middleware\auth.py" >nul 2>&1

REM ── models/ ───────────────────────────────────────────────────
echo [7/8] Moving models...
move /Y "demand_forecaster.py" "models\demand_forecaster.py" >nul 2>&1
move /Y "forecaster_eval.py"   "models\forecaster_eval.py"   >nul 2>&1
move /Y "queue_model.py"       "models\queue_model.py"       >nul 2>&1
move /Y "queue_validator.py"   "models\queue_validator.py"   >nul 2>&1

REM ── realtime/ ─────────────────────────────────────────────────
echo [8/8] Moving realtime and utils...
move /Y "google_places_client.py"  "realtime\google_places_client.py"  >nul 2>&1
move /Y "nrel_client.py"           "realtime\nrel_client.py"           >nul 2>&1
move /Y "ocpp_central.py"          "realtime\ocpp_central.py"          >nul 2>&1
move /Y "ocpp_simulator.py"        "realtime\ocpp_simulator.py"        >nul 2>&1
move /Y "openchargemap_client.py"  "realtime\openchargemap_client.py"  >nul 2>&1
move /Y "osm_places_client.py"     "realtime\osm_places_client.py"     >nul 2>&1

REM ── scripts/ ──────────────────────────────────────────────────
move /Y "deploy.py"        "scripts\deploy.sh"          >nul 2>&1
move /Y "deploy.sh"        "scripts\deploy.sh"          >nul 2>&1
move /Y "deploy"           "scripts\deploy.sh"          >nul 2>&1
move /Y "init_bigquery.py" "scripts\init_bigquery.py"   >nul 2>&1
move /Y "seed_bigquery.sh" "scripts\seed_bigquery.sh"   >nul 2>&1
move /Y "seed_bigquery"    "scripts\seed_bigquery.sh"   >nul 2>&1

REM ── tests/ ────────────────────────────────────────────────────
move /Y "conftest.py"               "tests\conftest.py"               >nul 2>&1
move /Y "test_advisor_api.py"       "tests\test_advisor_api.py"       >nul 2>&1
move /Y "test_api_paths.py"         "tests\test_api_paths.py"         >nul 2>&1
move /Y "test_data_quality_labels.py" "tests\test_data_quality_labels.py" >nul 2>&1
move /Y "test_discover_api.py"      "tests\test_discover_api.py"      >nul 2>&1
move /Y "test_forecaster.py"        "tests\test_forecaster.py"        >nul 2>&1
move /Y "test_geo_enricher.py"      "tests\test_geo_enricher.py"      >nul 2>&1
move /Y "test_provider_merge.py"    "tests\test_provider_merge.py"    >nul 2>&1
move /Y "test_queue_model.py"       "tests\test_queue_model.py"       >nul 2>&1
move /Y "test_station_registry.py"  "tests\test_station_registry.py"  >nul 2>&1

REM ── utils/ ────────────────────────────────────────────────────
move /Y "async_bq.py"       "utils\async_bq.py"       >nul 2>&1
move /Y "cache.py"          "utils\cache.py"           >nul 2>&1
move /Y "explainability.py" "utils\explainability.py"  >nul 2>&1
move /Y "geo_enricher.py"   "utils\geo_enricher.py"    >nul 2>&1
move /Y "normalizers.py"    "utils\normalizers.py"     >nul 2>&1
move /Y "observability.py"  "utils\observability.py"   >nul 2>&1
move /Y "provider_merge.py" "utils\provider_merge.py"  >nul 2>&1

REM ── .github/workflows/ ───────────────────────────────────────
move /Y "ci.yml" ".github\workflows\ci.yml" >nul 2>&1

REM ── Root-level renames ────────────────────────────────────────
echo Renaming root files...
if exist "requirements (1).txt" (
    copy /Y "requirements (1).txt" "requirements.txt" >nul
    del "requirements (1).txt" >nul 2>&1
    echo     requirements.txt renamed OK
)
if exist "requirements (1)" (
    copy /Y "requirements (1)" "requirements.txt" >nul
    del "requirements (1)" >nul 2>&1
    echo     requirements renamed OK
)
if exist "deploy (1).sh" del "deploy (1).sh" >nul 2>&1
if exist "deploy (1)"    del "deploy (1)"    >nul 2>&1

REM ── Create all __init__.py files (empty, required by Python) ──
echo Creating __init__.py files...
type nul > "agents\__init__.py"
type nul > "api\__init__.py"
type nul > "llm\__init__.py"
type nul > "middleware\__init__.py"
type nul > "models\__init__.py"
type nul > "realtime\__init__.py"
type nul > "tests\__init__.py"
type nul > "utils\__init__.py"
echo     All 8 __init__.py files created.

REM ── Rename _env.example if needed ────────────────────────────
if exist "_env.example" (
    if not exist ".env.example" copy /Y "_env.example" ".env.example" >nul
)

REM ── Clean up numbered duplicate __init__ files ────────────────
echo Cleaning up duplicate __init__ files...
del "__init__ (1).py" 2>nul
del "__init__ (2).py" 2>nul
del "__init__ (3).py" 2>nul
del "__init__ (4).py" 2>nul
del "__init__ (5).py" 2>nul
del "__init__ (6).py" 2>nul
del "__init__ (1)"    2>nul
del "__init__ (2)"    2>nul
del "__init__ (3)"    2>nul
del "__init__ (4)"    2>nul
del "__init__ (5)"    2>nul
del "__init__ (6)"    2>nul
del "__init__"        2>nul

REM ── Verify final structure ────────────────────────────────────
echo.
echo === Verifying structure ===
echo.
echo Root files:
dir /B *.py *.txt *.yml *.yaml *.md 2>nul | findstr /V "__init__"
echo.
echo Subdirectories:
for %%d in (agents api frontend llm middleware models realtime scripts tests utils) do (
    echo   %%d\
    dir /B "%%d\" 2>nul | for /F "tokens=*" %%f in ('more') do echo     %%f
)
echo.
echo === Setup complete! ===
echo.
echo Next steps:
echo   1. Copy .env.example to .env and set GOOGLE_CLOUD_PROJECT
echo   2. pip install -r requirements.txt
echo   3. pytest tests/ -v
echo   4. python -m uvicorn api.main:app --reload --port 8080
echo.
pause
