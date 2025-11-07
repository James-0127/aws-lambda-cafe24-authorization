"""
This module reads configuration from environment variables.
"""
import os
import json
import time
import boto3
from typing import Dict

PROFILE = os.getenv("AWS_PROFILE")
REGION  = os.getenv("AWS_REGION")

if PROFILE:
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
else:
    session = boto3.Session(region_name=REGION)

_SM = session.client("secretsmanager")
_CACHE = {}
_CACHE_TS = 0.0
_CACHE_TTL = int(os.getenv("DB_SECRET_CACHE_TTL", "600"))  # 10분

def _read_user_pass_from_sm(secret_arn: str) -> Dict[str, str]:
    resp = _SM.get_secret_value(SecretId=secret_arn)
    payload = resp.get("SecretString") or "{}"
    data = json.loads(payload)

    return {
        "username": data["username"],
        "password": data["password"]
    }

def _get_user_pass(secret_arn: str) -> Dict[str, str]:
    global _CACHE_TS
    now = time.time()
    if _CACHE and (now - _CACHE_TS) < _CACHE_TTL:
        return _CACHE
    creds = _read_user_pass_from_sm(secret_arn)
    _CACHE.clear(); _CACHE.update(creds); _CACHE_TS = now
    return creds


def get_pg_config() -> Dict[str, str]:
    """
    host/port/dbname 은 ENV(또는 SSM Parameter Store)에서,
    username/password 는 Secrets Manager에서.
    """
    host = os.environ["PGHOST"]
    port = os.environ.get("PGPORT", "5432")
    db   = os.environ.get("PGDATABASE", "postgres")
    secret_arn = os.environ["DB_SECRET_ARN"]
    creds = _get_user_pass(secret_arn)

    return {
        "host": host,
        "port": port,
        "user": creds["username"],
        "password": creds["password"],
        "database": db
    }

def get_expected_state_secret():
    """
    OAuth state 검증에 사용 (콜백 핸들러용)
    """
    return os.environ.get("EXPECTED_STATE_SECRET")
