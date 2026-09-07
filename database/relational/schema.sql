PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS patients(id TEXT PRIMARY KEY, alias TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS measurements(
  id INTEGER PRIMARY KEY, patient_id TEXT NOT NULL REFERENCES patients(id),
  measured_at TEXT NOT NULL, systolic REAL, diastolic REAL, heart_rate REAL, adherence REAL,
  dataset TEXT NOT NULL CHECK(dataset IN ('treino','monitoramento')),
  expected_case TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evaluations(
  measurement_id INTEGER NOT NULL REFERENCES measurements(id), model_version TEXT NOT NULL,
  run_id TEXT NOT NULL, label TEXT NOT NULL, score REAL,
  PRIMARY KEY(measurement_id,model_version)
);
CREATE TABLE IF NOT EXISTS alerts(
  id TEXT PRIMARY KEY, measurement_id INTEGER NOT NULL REFERENCES measurements(id),
  run_id TEXT NOT NULL, model_version TEXT NOT NULL, reason TEXT NOT NULL, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs(
  id TEXT PRIMARY KEY, started TEXT NOT NULL, finished TEXT, status TEXT NOT NULL,
  processed INTEGER NOT NULL DEFAULT 0, error_code TEXT
);
CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY, collection TEXT NOT NULL, body TEXT NOT NULL, delivered INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS measurements_dataset ON measurements(dataset,id);
CREATE INDEX IF NOT EXISTS outbox_delivered ON outbox(delivered);
