"""
scripts/init_bigquery.py  —  Bootstrap the ev_advisor_core BigQuery dataset.

Creates all tables for the v2.2 dynamic schema:
  base_geo_cache, mobility_inventory_raw, mobility_inventory_curated,
  live_port_status, zone_profiles, business_signals, advisor_scores,
  request_logs, station_registry, charger_events, session_history

Safe to re-run: skips existing tables with `exist_ok=True`.
Does NOT drop the old mcp_mobility dataset — keep it until new schema is verified.

Usage:
  python scripts/init_bigquery.py [--project YOUR_PROJECT_ID] [--dataset ev_advisor_core]
"""

import argparse
import os
import sys

try:
    from google.cloud import bigquery
except ImportError:
    print("ERROR: google-cloud-bigquery not installed. Run: pip install google-cloud-bigquery")
    sys.exit(1)


def get_schema(table_name: str):
    SCHEMAS = {
        "base_geo_cache": [
            bigquery.SchemaField("city_key",        "STRING",  mode="REQUIRED"),
            bigquery.SchemaField("query_text",       "STRING"),
            bigquery.SchemaField("display_name",     "STRING"),
            bigquery.SchemaField("country_code",     "STRING"),
            bigquery.SchemaField("lat",              "FLOAT64"),
            bigquery.SchemaField("lon",              "FLOAT64"),
            bigquery.SchemaField("bbox",             "JSON"),
            bigquery.SchemaField("neighborhoods",    "JSON"),
            bigquery.SchemaField("source",           "STRING"),
            bigquery.SchemaField("fetched_at",       "TIMESTAMP"),
            bigquery.SchemaField("cache_expires_at", "TIMESTAMP"),
        ],
        "mobility_inventory_raw": [
            bigquery.SchemaField("record_id",       "STRING",  mode="REQUIRED"),
            bigquery.SchemaField("city_key",        "STRING"),
            bigquery.SchemaField("provider",        "STRING"),
            bigquery.SchemaField("fetched_at",      "TIMESTAMP"),
            bigquery.SchemaField("raw_payload",     "JSON"),
        ],
        "mobility_inventory_curated": [
            bigquery.SchemaField("record_id",       "STRING",  mode="REQUIRED"),
            bigquery.SchemaField("city_key",        "STRING"),
            bigquery.SchemaField("snapshot_date",   "DATE"),
            bigquery.SchemaField("type",            "STRING"),
            bigquery.SchemaField("name",            "STRING"),
            bigquery.SchemaField("subtypes",        "STRING",  mode="REPEATED"),
            bigquery.SchemaField("lat",             "FLOAT64"),
            bigquery.SchemaField("lon",             "FLOAT64"),
            bigquery.SchemaField("address",         "STRING"),
            bigquery.SchemaField("operator",        "STRING"),
            bigquery.SchemaField("connector_types", "STRING",  mode="REPEATED"),
            bigquery.SchemaField("power_kw",        "FLOAT64"),
            bigquery.SchemaField("total_ports",     "INT64"),
            bigquery.SchemaField("available_ports", "INT64"),
            bigquery.SchemaField("status",          "STRING"),
            bigquery.SchemaField("price_info",      "STRING"),
            bigquery.SchemaField("data_source",     "STRING"),
            bigquery.SchemaField("data_quality",    "STRING"),
            bigquery.SchemaField("fallback_reason", "STRING"),
            bigquery.SchemaField("last_updated",    "TIMESTAMP"),
        ],
        "live_port_status": [
            bigquery.SchemaField("station_id",    "STRING",    mode="REQUIRED"),
            bigquery.SchemaField("port_id",       "STRING"),
            bigquery.SchemaField("status",        "STRING"),
            bigquery.SchemaField("last_updated",  "TIMESTAMP"),
            bigquery.SchemaField("session_id",    "STRING"),
            bigquery.SchemaField("session_start", "TIMESTAMP"),
        ],
        "zone_profiles": [
            bigquery.SchemaField("city_key",              "STRING"),
            bigquery.SchemaField("zone_id",               "STRING"),
            bigquery.SchemaField("zone_name",             "STRING"),
            bigquery.SchemaField("city",                  "STRING"),
            bigquery.SchemaField("snapshot_date",         "DATE"),
            bigquery.SchemaField("lat",                   "FLOAT64"),
            bigquery.SchemaField("lon",                   "FLOAT64"),
            bigquery.SchemaField("population_proxy",      "FLOAT64"),
            bigquery.SchemaField("ev_adoption_proxy",     "FLOAT64"),
            bigquery.SchemaField("traffic_proxy",         "FLOAT64"),
            bigquery.SchemaField("parking_presence_proxy","FLOAT64"),
            bigquery.SchemaField("charger_density",       "FLOAT64"),
            bigquery.SchemaField("competitor_density",    "FLOAT64"),
            bigquery.SchemaField("confidence_score",      "FLOAT64"),
        ],
        "business_signals": [
            bigquery.SchemaField("city_key",          "STRING"),
            bigquery.SchemaField("zone_id",           "STRING"),
            bigquery.SchemaField("snapshot_date",     "DATE"),
            bigquery.SchemaField("signal_name",       "STRING"),
            bigquery.SchemaField("signal_value",      "FLOAT64"),
            bigquery.SchemaField("signal_source",     "STRING"),
            bigquery.SchemaField("confidence",        "FLOAT64"),
        ],
        "advisor_scores": [
            bigquery.SchemaField("city_key",                  "STRING"),
            bigquery.SchemaField("zone_id",                   "STRING"),
            bigquery.SchemaField("snapshot_date",             "DATE"),
            bigquery.SchemaField("demand_score",              "FLOAT64"),
            bigquery.SchemaField("competition_score",         "FLOAT64"),
            bigquery.SchemaField("accessibility_score",       "FLOAT64"),
            bigquery.SchemaField("parking_support_score",     "FLOAT64"),
            bigquery.SchemaField("grid_score",                "FLOAT64"),
            bigquery.SchemaField("roi_score",                 "FLOAT64"),
            bigquery.SchemaField("viability_score",           "FLOAT64"),
            bigquery.SchemaField("confidence_score",          "FLOAT64"),
            bigquery.SchemaField("recommended_station_type",  "STRING"),
            bigquery.SchemaField("recommended_port_count",    "INT64"),
            bigquery.SchemaField("recommended_connector_mix", "STRING",  mode="REPEATED"),
            bigquery.SchemaField("real_inputs",               "JSON"),
            bigquery.SchemaField("modeled_inputs",            "JSON"),
            bigquery.SchemaField("explanation",               "STRING"),
        ],
        "request_logs": [
            bigquery.SchemaField("request_id",           "STRING"),
            bigquery.SchemaField("route",                "STRING"),
            bigquery.SchemaField("city_key",             "STRING"),
            bigquery.SchemaField("provider_calls",       "INT64"),
            bigquery.SchemaField("cache_hit",            "BOOL"),
            bigquery.SchemaField("fallback_used",        "BOOL"),
            bigquery.SchemaField("data_quality_summary", "JSON"),
            bigquery.SchemaField("latency_ms",           "INT64"),
            bigquery.SchemaField("status_code",          "INT64"),
            bigquery.SchemaField("request_ts",           "TIMESTAMP"),
        ],
        "station_registry": [
            bigquery.SchemaField("station_id",      "STRING", mode="REQUIRED"),
            bigquery.SchemaField("name",            "STRING"),
            bigquery.SchemaField("lat",             "FLOAT64"),
            bigquery.SchemaField("lon",             "FLOAT64"),
            bigquery.SchemaField("city",            "STRING"),
            bigquery.SchemaField("zip_code",        "STRING"),
            bigquery.SchemaField("network",         "STRING"),
            bigquery.SchemaField("kw",              "INT64"),
            bigquery.SchemaField("total_ports",     "INT64"),
            bigquery.SchemaField("connector_types", "STRING"),
            bigquery.SchemaField("data_source",     "STRING"),
            bigquery.SchemaField("is_active",       "BOOL"),
        ],
        "charger_events": [
            bigquery.SchemaField("event_id",    "STRING"),
            bigquery.SchemaField("station_id",  "STRING"),
            bigquery.SchemaField("port_id",     "STRING"),
            bigquery.SchemaField("event_type",  "STRING"),
            bigquery.SchemaField("status",      "STRING"),
            bigquery.SchemaField("error_code",  "STRING"),
            bigquery.SchemaField("timestamp",   "TIMESTAMP"),
        ],
        "session_history": [
            bigquery.SchemaField("session_id",       "STRING"),
            bigquery.SchemaField("station_id",       "STRING"),
            bigquery.SchemaField("port_id",          "STRING"),
            bigquery.SchemaField("start_time",       "TIMESTAMP"),
            bigquery.SchemaField("end_time",         "TIMESTAMP"),
            bigquery.SchemaField("energy_kwh",       "FLOAT64"),
            bigquery.SchemaField("duration_minutes", "INT64"),
        ],
    }
    return SCHEMAS.get(table_name)


# Partition + clustering config per table
_PARTITION = {
    "base_geo_cache":            ("fetched_at",    ["city_key"]),
    "mobility_inventory_raw":    ("fetched_at",    ["provider", "city_key"]),
    "mobility_inventory_curated":("snapshot_date", ["city_key", "type", "data_source"]),
    "zone_profiles":             ("snapshot_date", ["city_key"]),
    "business_signals":          ("snapshot_date", ["city_key", "zone_id"]),
    "advisor_scores":            ("snapshot_date", ["city_key", "zone_id"]),
    "request_logs":              ("request_ts",    ["route", "city_key"]),
    "charger_events":            ("timestamp",     ["station_id"]),
    "session_history":           ("start_time",    ["station_id"]),
}


def create_table(client, project, dataset, table_name, location):
    schema = get_schema(table_name)
    if schema is None:
        print(f"  SKIP {table_name} — no schema defined")
        return

    table_ref = f"{project}.{dataset}.{table_name}"
    table_obj = bigquery.Table(table_ref, schema=schema)

    if table_name in _PARTITION:
        part_field, cluster_fields = _PARTITION[table_name]
        table_obj.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field=part_field,
            require_partition_filter=True,
        )
        table_obj.clustering_fields = cluster_fields[:4]  # BQ max 4

    try:
        client.create_table(table_obj, exists_ok=True)
        print(f"  OK  {table_name}")
    except Exception as e:
        print(f"  ERR {table_name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Bootstrap ev_advisor_core BigQuery dataset")
    parser.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
    parser.add_argument("--dataset", default=os.environ.get("BIGQUERY_DATASET", "ev_advisor_core"))
    parser.add_argument("--location", default=os.environ.get("BIGQUERY_LOCATION", "US"))
    args = parser.parse_args()

    if not args.project:
        print("ERROR: --project or GOOGLE_CLOUD_PROJECT env var is required")
        sys.exit(1)

    bq = bigquery.Client(project=args.project)

    # Create dataset (safe if already exists)
    ds_ref = bigquery.Dataset(f"{args.project}.{args.dataset}")
    ds_ref.location = args.location
    ds_ref.description = "EV Advisor Core — dynamic global schema v2.2"
    try:
        bq.create_dataset(ds_ref, exists_ok=True)
        print(f"Dataset: {args.project}.{args.dataset} ({args.location})")
    except Exception as e:
        print(f"Dataset creation error: {e}")
        sys.exit(1)

    # Create all tables
    tables = list(get_schema.__code__.co_consts)  # not reliable; use explicit list
    table_list = [
        "base_geo_cache", "mobility_inventory_raw", "mobility_inventory_curated",
        "live_port_status", "zone_profiles", "business_signals", "advisor_scores",
        "request_logs", "station_registry", "charger_events", "session_history",
    ]
    print(f"Creating {len(table_list)} tables…")
    for t in table_list:
        create_table(bq, args.project, args.dataset, t, args.location)

    print(f"\nDone. Dataset: {args.project}.{args.dataset}")
    print("Note: old mcp_mobility dataset preserved — decommission after verification.")


if __name__ == "__main__":
    main()
