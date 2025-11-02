import os
import json
from datetime import datetime, timezone
import psycopg
from psycopg.rows import dict_row

if os.environ.get("AWS_EXECUTION_ENV") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=".env.local")
    except Exception as e:
        print("dotenv load skipped or failed:", e)

def _json_response(status_code: int, body_obj: dict):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body_obj, default=str),
    }

def lambda_handler(event, context):
    qs = event.get("queryStringParameters") or {}
    code = qs.get("code")
    state = qs.get("state")

    if not code or not state:
        return _json_response(400, {
            "ok": False,
            "message": "Missing required query parameters: code, state"
        })

    expected_prefix = os.environ.get("EXPECTED_STATE_SECRET")
    if (not expected_prefix) or (not state.startswith(expected_prefix)):
        return _json_response(403, {
            "ok": False,
            "message": "Invalid state"
        })

    pg_host = os.environ.get("PGHOST")
    pg_port = os.environ.get("PGPORT", "5432")
    pg_user = os.environ.get("PGUSER")
    pg_password = os.environ.get("PGPASSWORD")
    pg_database = os.environ.get("PGDATABASE")

    if not all([pg_host, pg_port, pg_user, pg_password, pg_database]):
        return _json_response(500, {
            "ok": False,
            "message": "Database environment variables are not fully set"
        })

    dsn = (
        f"postgresql://{pg_user}:{pg_password}"
        f"@{pg_host}:{pg_port}/{pg_database}"
    )

    try:
        with psycopg.connect(
            dsn,
            sslmode="require",
            row_factory=dict_row
        ) as conn:
            with conn.cursor() as cur:
                insert_sql = """
                    INSERT INTO cafe24.authorization_codes (code, state, received_at)
                    VALUES (%s, %s, %s)
                    RETURNING id, received_at;
                """
                now_ts = datetime.now(timezone.utc)
                cur.execute(insert_sql, (code, state, now_ts))
                row = cur.fetchone()
                conn.commit()

        return _json_response(200, {
            "ok": True,
            "message": "Authorization code stored",
            "data": {
                "id": row["id"],
                "code": code,
                "state": state,
                "received_at": row["received_at"],
            }
        })

    except Exception as e:
        print("DB error:", repr(e))
        return _json_response(500, {
            "ok": False,
            "message": "Database insert failed",
            "error": str(e)
        })