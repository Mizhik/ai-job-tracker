DROP INDEX idx_jobs_user_created_id;

ALTER TABLE jobs
    DROP CONSTRAINT jobs_currency_format,
    DROP CONSTRAINT jobs_salary_period,
    DROP CONSTRAINT jobs_salary_nonnegative,
    DROP CONSTRAINT jobs_salary_range,
    DROP COLUMN currency,
    DROP COLUMN salary_period;
