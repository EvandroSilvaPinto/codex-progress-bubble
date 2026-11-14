CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  read_hash TEXT NOT NULL,
  write_hash TEXT NOT NULL,
  payload TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  hard_expires_at INTEGER NOT NULL,
  completed_at INTEGER,
  revoked INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires_at);
