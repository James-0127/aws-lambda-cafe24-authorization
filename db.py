"""
This moudle provides database access functions for Cafe24 Oauth tokens.
"""
from datetime import datetime, timezone, timedelta
import psycopg
from psycopg.rows import dict_row
from settings import get_pg_config

KST = timezone(timedelta(hours=9))

class DBError(Exception):
    pass

def _dsn_from_env():
    """
    Constructs the Postgres DSN from environment variables.
    """
    cfg = get_pg_config()
    if not all([cfg["host"], cfg["port"], cfg["user"], cfg["password"], cfg["database"]]):
        raise DBError("Database environment variables are not fully set")
    return (
        f"postgresql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )

def execute_insert_authcode(code, state):
    """
    params_tuple 순서는 token_store.upsert_token()에서 만들어서 넘김.
    실제 upsert SQL만 여기서 실행.
    """
    insert_sql = """
        INSERT INTO cafe24.authorization_codes (code, state, received_at)
        VALUES (%s, %s, %s)
        RETURNING id, received_at;
    """
    
    params = (code, state, datetime.now(KST))

    dsn = _dsn_from_env()
    with psycopg.connect(dsn, sslmode="require", row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            now_ts = datetime.now(KST)
            cur.execute(insert_sql, params)
            row = cur.fetchone()
            conn.commit()
    return row
