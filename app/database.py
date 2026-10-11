import sqlite3, json
from contextlib import contextmanager
from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS generations (
 id TEXT PRIMARY KEY, created_at TEXT NOT NULL, prompt TEXT NOT NULL,
 detected_concept TEXT NOT NULL, purpose TEXT NOT NULL, grade_group TEXT,
 complexity TEXT NOT NULL, color_requirement TEXT NOT NULL, width INTEGER NOT NULL,
 height INTEGER NOT NULL, selected_pipeline TEXT NOT NULL, elapsed_ms REAL NOT NULL,
 output_file TEXT NOT NULL, output_size_bytes INTEGER NOT NULL, status TEXT NOT NULL,
 quality_checks_json TEXT NOT NULL, fallback_used INTEGER NOT NULL DEFAULT 0,
 fallback_pipeline TEXT, reason TEXT
);
CREATE TABLE IF NOT EXISTS benchmark_runs (
 id TEXT PRIMARY KEY, created_at TEXT NOT NULL, test_case_id TEXT NOT NULL,
 baseline_pipeline TEXT NOT NULL, optimized_pipeline TEXT NOT NULL,
 baseline_elapsed_ms REAL NOT NULL, optimized_elapsed_ms REAL NOT NULL,
 baseline_size_bytes INTEGER NOT NULL, optimized_size_bytes INTEGER NOT NULL,
 baseline_quality_status TEXT NOT NULL, optimized_quality_status TEXT NOT NULL,
 estimated_cost REAL, cost_assumptions TEXT, notes TEXT,
 baseline_width INTEGER, baseline_height INTEGER, optimized_width INTEGER,
 optimized_height INTEGER, fallback_count INTEGER NOT NULL DEFAULT 0
);
"""
def connect():
    con=sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory=sqlite3.Row
    return con
def init_db():
    with connect() as con:
        con.executescript(SCHEMA)
        generation_columns={row[1] for row in con.execute("PRAGMA table_info(generations)")}
        if "fallback_pipeline" not in generation_columns:
            con.execute("ALTER TABLE generations ADD COLUMN fallback_pipeline TEXT")
        if "reason" not in generation_columns:
            con.execute("ALTER TABLE generations ADD COLUMN reason TEXT")
        benchmark_columns={row[1] for row in con.execute("PRAGMA table_info(benchmark_runs)")}
        for column in ("baseline_width", "baseline_height", "optimized_width", "optimized_height"):
            if column not in benchmark_columns:
                con.execute(f"ALTER TABLE benchmark_runs ADD COLUMN {column} INTEGER")
        if "fallback_count" not in benchmark_columns:
            con.execute("ALTER TABLE benchmark_runs ADD COLUMN fallback_count INTEGER NOT NULL DEFAULT 0")
@contextmanager
def db():
    con=connect()
    try:
        yield con
        con.commit()
    finally: con.close()
