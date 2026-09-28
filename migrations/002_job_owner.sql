ALTER TABLE jobs
    ADD COLUMN user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX idx_jobs_user_id ON jobs(user_id);
