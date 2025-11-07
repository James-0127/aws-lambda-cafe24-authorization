import os
import json
from db import execute_insert_authcode

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

    try:
        row = execute_insert_authcode(code, state)

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