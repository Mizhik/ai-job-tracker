DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM jobs
        WHERE salary_min < 0
           OR salary_max < 0
           OR (salary_min IS NOT NULL AND salary_max IS NOT NULL AND salary_min > salary_max)
    ) THEN
        RAISE EXCEPTION 'Existing jobs contain invalid salary ranges; correct them before applying 003_job_contract';
    END IF;
END
$$;

ALTER TABLE jobs
    ADD COLUMN currency VARCHAR(3),
    ADD COLUMN salary_period VARCHAR(10),
    ADD CONSTRAINT jobs_currency_format
        CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
    ADD CONSTRAINT jobs_salary_period
        CHECK (salary_period IS NULL OR salary_period IN ('hour', 'month', 'year')),
    ADD CONSTRAINT jobs_salary_nonnegative
        CHECK ((salary_min IS NULL OR salary_min >= 0) AND (salary_max IS NULL OR salary_max >= 0)),
    ADD CONSTRAINT jobs_salary_range
        CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max);

CREATE INDEX idx_jobs_user_created_id
    ON jobs (user_id, created_at DESC, id DESC);
