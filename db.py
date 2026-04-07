import os
import sqlite3
import json

DB_DIR = os.path.expanduser("~/Pictures/icloud-triage/app-data")
DB_PATH = os.path.join(DB_DIR, "db.sqlite")


def _connect():
    os.makedirs(DB_DIR, mode=0o700, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DB_DIR, mode=0o700, exist_ok=True)
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            apple_id TEXT NOT NULL,
            password TEXT NOT NULL,
            session_data TEXT,
            auth_complete INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            media_type TEXT,
            taken_at DATETIME,
            size_bytes INTEGER,
            local_path TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            is_favorite INTEGER NOT NULL DEFAULT 0,
            keep_forever INTEGER NOT NULL DEFAULT 0,
            downloaded_at DATETIME,
            deleted_at DATETIME,
            batch_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at DATETIME NOT NULL DEFAULT (datetime('now')),
            completed_at DATETIME,
            asset_count INTEGER,
            deleted_count INTEGER
        );
    """)
    # Migrate: add auth_complete if missing (existing DBs)
    try:
        conn.execute("ALTER TABLE credentials ADD COLUMN auth_complete INTEGER NOT NULL DEFAULT 0")
    except Exception:
        pass  # column already exists
    # Migrate: existing 'downloaded' and 'to_iphoto' rows become 'archive'
    conn.execute("UPDATE assets SET status='archive' WHERE status IN ('downloaded', 'to_iphoto')")
    conn.commit()
    conn.close()
    try:
        os.chmod(DB_PATH, 0o600)
    except OSError:
        pass


# --- Credentials ---

def get_credentials():
    conn = _connect()
    row = conn.execute("SELECT apple_id, password FROM credentials WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def save_credentials(apple_id, password):
    conn = _connect()
    conn.execute(
        "INSERT INTO credentials (id, apple_id, password) VALUES (1, ?, ?)"
        " ON CONFLICT(id) DO UPDATE SET apple_id=excluded.apple_id, password=excluded.password",
        (apple_id, password),
    )
    conn.commit()
    conn.close()


# --- Session ---

def get_session():
    conn = _connect()
    row = conn.execute("SELECT session_data FROM credentials WHERE id = 1").fetchone()
    conn.close()
    if row and row["session_data"]:
        return json.loads(row["session_data"])
    return None


def save_session(session_data):
    conn = _connect()
    conn.execute(
        "UPDATE credentials SET session_data = ? WHERE id = 1",
        (json.dumps(session_data),),
    )
    conn.commit()
    conn.close()


def clear_session():
    conn = _connect()
    conn.execute("UPDATE credentials SET session_data = NULL, auth_complete = 0 WHERE id = 1")
    conn.commit()
    conn.close()


def set_auth_complete():
    conn = _connect()
    conn.execute("UPDATE credentials SET auth_complete = 1 WHERE id = 1")
    conn.commit()
    conn.close()


def is_auth_complete():
    conn = _connect()
    row = conn.execute("SELECT auth_complete FROM credentials WHERE id = 1").fetchone()
    conn.close()
    return bool(row and row["auth_complete"])


# --- Asset helpers ---

def upsert_asset(asset_id, filename, media_type, taken_at, size_bytes, is_favorite):
    conn = _connect()
    conn.execute("""
        INSERT INTO assets (id, filename, media_type, taken_at, size_bytes, is_favorite)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            filename=excluded.filename,
            media_type=excluded.media_type,
            taken_at=excluded.taken_at,
            size_bytes=excluded.size_bytes,
            is_favorite=excluded.is_favorite
    """, (asset_id, filename, media_type, taken_at, size_bytes, is_favorite))
    conn.commit()
    conn.close()


def get_asset(asset_id):
    conn = _connect()
    row = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_local_path(asset_id, local_path):
    conn = _connect()
    conn.execute("UPDATE assets SET local_path=? WHERE id=?", (local_path, asset_id))
    conn.commit()
    conn.close()


# --- Pipeline status setters ---

def get_eligible_batch_asset_ids():
    conn = _connect()
    rows = conn.execute("""
        SELECT id FROM assets
        WHERE status='pending' AND keep_forever=0
        ORDER BY taken_at ASC LIMIT 10
    """).fetchall()
    conn.close()
    return [r["id"] for r in rows]


def get_in_triage_assets():
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM assets WHERE status='in_triage' ORDER BY taken_at ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_downloading_next_assets():
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM assets WHERE status='downloading_next' ORDER BY taken_at ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_status_in_triage(asset_ids):
    conn = _connect()
    conn.executemany(
        "UPDATE assets SET status='in_triage' WHERE id=?",
        [(aid,) for aid in asset_ids],
    )
    conn.commit()
    conn.close()


def set_status_downloading_next(asset_ids):
    conn = _connect()
    conn.executemany(
        "UPDATE assets SET status='downloading_next' WHERE id=?",
        [(aid,) for aid in asset_ids],
    )
    conn.commit()
    conn.close()


def set_status_keep_forever(asset_id, local_path):
    conn = _connect()
    conn.execute(
        "UPDATE assets SET status='keep_forever', keep_forever=1, local_path=?, downloaded_at=datetime('now') WHERE id=?",
        (local_path, asset_id),
    )
    conn.commit()
    conn.close()


def set_status_archive(asset_id, local_path):
    conn = _connect()
    conn.execute(
        "UPDATE assets SET status='archive', local_path=?, downloaded_at=datetime('now'), deleted_at=datetime('now') WHERE id=?",
        (local_path, asset_id),
    )
    conn.commit()
    conn.close()


def set_status_for_deletion(asset_id, local_path):
    conn = _connect()
    conn.execute(
        "UPDATE assets SET status='for_deletion', local_path=?, downloaded_at=datetime('now'), deleted_at=datetime('now') WHERE id=?",
        (local_path, asset_id),
    )
    conn.commit()
    conn.close()


# --- Keep-forever strip ---

def get_keep_forever_assets(limit=20):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM assets WHERE keep_forever=1 ORDER BY downloaded_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_keep_forever_total_bytes():
    conn = _connect()
    row = conn.execute(
        "SELECT SUM(size_bytes) as total FROM assets WHERE keep_forever=1"
    ).fetchone()
    conn.close()
    return row["total"] or 0


# --- Stats ---

def get_pending_stats():
    conn = _connect()
    row = conn.execute("""
        SELECT COUNT(*) as total, SUM(size_bytes) as total_bytes
        FROM assets
        WHERE status='pending'
    """).fetchone()
    rows = conn.execute("""
        SELECT filename FROM assets WHERE status='pending'
    """).fetchall()
    conn.close()

    by_ext = {}
    for r in rows:
        fn = r["filename"] or ""
        dot = fn.rfind(".")
        ext = fn[dot+1:].upper() if dot >= 0 else "OTHER"
        by_ext[ext] = by_ext.get(ext, 0) + 1

    return {
        "total": row["total"] or 0,
        "total_bytes": row["total_bytes"] or 0,
        "by_extension": by_ext,
    }


def get_dashboard_stats():
    conn = _connect()
    pending_row = conn.execute("""
        SELECT COUNT(*) as cnt, SUM(size_bytes) as bytes
        FROM assets WHERE status='pending'
    """).fetchone()
    kf_row = conn.execute("""
        SELECT COUNT(*) as cnt, SUM(size_bytes) as bytes
        FROM assets WHERE keep_forever=1
    """).fetchone()
    conn.close()
    return {
        "pending_count": pending_row["cnt"] or 0,
        "pending_bytes": pending_row["bytes"] or 0,
        "keep_forever_count": kf_row["cnt"] or 0,
        "keep_forever_bytes": kf_row["bytes"] or 0,
    }


# --- Legacy helpers (kept for batch history) ---

def get_batch_assets(batch_id):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM assets WHERE batch_id = ? ORDER BY taken_at ASC",
        (batch_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_current_batch_id():
    conn = _connect()
    row = conn.execute("SELECT MAX(id) as bid FROM batches").fetchone()
    conn.close()
    return row["bid"] if row else None


def mark_deleted(asset_id):
    conn = _connect()
    conn.execute(
        "UPDATE assets SET status='for_deletion', deleted_at=datetime('now') WHERE id=?",
        (asset_id,),
    )
    conn.commit()
    conn.close()


def create_batch():
    conn = _connect()
    cur = conn.execute("INSERT INTO batches (started_at) VALUES (datetime('now'))")
    batch_id = cur.lastrowid
    conn.commit()
    conn.close()
    return batch_id


def complete_batch(batch_id, asset_count):
    conn = _connect()
    conn.execute(
        "UPDATE batches SET completed_at=datetime('now'), asset_count=? WHERE id=?",
        (asset_count, batch_id),
    )
    conn.commit()
    conn.close()


def assign_batch(asset_ids, batch_id):
    conn = _connect()
    conn.executemany(
        "UPDATE assets SET batch_id=? WHERE id=?",
        [(batch_id, aid) for aid in asset_ids],
    )
    conn.commit()
    conn.close()
