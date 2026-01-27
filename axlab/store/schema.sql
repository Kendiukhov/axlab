CREATE TABLE IF NOT EXISTS artifacts (
    digest TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    size INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    spec_json TEXT NOT NULL,
    battery_config_json TEXT NOT NULL,
    manifest_digest TEXT NOT NULL,
    results_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS axioms (
    run_id TEXT NOT NULL,
    axiom_id TEXT NOT NULL,
    left_term TEXT NOT NULL,
    right_term TEXT NOT NULL,
    symmetry_class TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, axiom_id)
);

CREATE TABLE IF NOT EXISTS models (
    run_id TEXT NOT NULL,
    axiom_id TEXT NOT NULL,
    size INTEGER NOT NULL,
    status TEXT NOT NULL,
    fingerprint TEXT,
    candidates INTEGER NOT NULL,
    elapsed_seconds REAL NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, axiom_id, size)
);

CREATE TABLE IF NOT EXISTS implications (
    run_id TEXT NOT NULL,
    axiom_id TEXT NOT NULL,
    theory TEXT NOT NULL,
    status TEXT NOT NULL,
    checked_max_size INTEGER NOT NULL,
    counterexample_size INTEGER,
    counterexample_fingerprint TEXT,
    proof_status TEXT,
    proof_elapsed_seconds REAL,
    proof_steps_json TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, axiom_id, theory)
);

CREATE TABLE IF NOT EXISTS metrics (
    run_id TEXT NOT NULL,
    axiom_id TEXT NOT NULL,
    name TEXT NOT NULL,
    value REAL,
    value_json TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, axiom_id, name)
);

CREATE TABLE IF NOT EXISTS notes (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    axiom_id TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);
