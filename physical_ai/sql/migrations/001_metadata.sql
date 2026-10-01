CREATE TABLE IF NOT EXISTS dataset (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    version TEXT,
    source_url TEXT NOT NULL,
    license TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS file_asset (
    id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES dataset(id),
    relative_path TEXT NOT NULL,
    sha256 CHAR(64),
    size_bytes BIGINT CHECK (size_bytes >= 0),
    UNIQUE (dataset_id, relative_path)
);

CREATE TABLE IF NOT EXISTS variable_catalog (
    id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES dataset(id),
    variable_name TEXT NOT NULL,
    semantic_role TEXT NOT NULL CHECK (semantic_role IN
        ('STATE', 'ACTION', 'CONTEXT', 'LABEL', 'EVAL_ONLY', 'IGNORE')),
    unit TEXT,
    description TEXT,
    UNIQUE (dataset_id, variable_name)
);

CREATE TABLE IF NOT EXISTS dataset_run (
    id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES dataset(id),
    external_run_id TEXT NOT NULL,
    split TEXT CHECK (split IN ('train', 'validation', 'test')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (dataset_id, external_run_id)
);

CREATE TABLE IF NOT EXISTS preprocess_profile (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    config JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feature_set (
    id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES dataset(id),
    preprocess_profile_id BIGINT REFERENCES preprocess_profile(id),
    name TEXT NOT NULL,
    manifest JSONB NOT NULL,
    UNIQUE (dataset_id, name)
);

CREATE TABLE IF NOT EXISTS experiment (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    config JSONB NOT NULL,
    git_commit CHAR(40),
    seed INTEGER,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS metric (
    id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiment(id),
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    scope JSONB NOT NULL DEFAULT '{}'::jsonb
);

