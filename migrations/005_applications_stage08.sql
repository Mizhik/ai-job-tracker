-- Migration 005: Applications Stage 08
-- Preflight checks on existing rows before applying structural changes
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'applications') THEN
        -- 1. Check for NULL owner/job/applied_at
        IF EXISTS (
            SELECT 1 FROM applications
            WHERE user_id IS NULL OR job_id IS NULL OR applied_at IS NULL
        ) THEN
            RAISE EXCEPTION 'Preflight failed: existing applications rows contain NULL user_id, job_id, or applied_at';
        END IF;

        -- 2. Check for legacy NEW status
        IF EXISTS (
            SELECT 1 FROM applications WHERE UPPER(status::text) = 'NEW'
        ) THEN
            RAISE EXCEPTION 'Preflight failed: existing applications rows contain legacy NEW status';
        END IF;

        -- 3. Check for invalid or unmappable status
        IF EXISTS (
            SELECT 1 FROM applications
            WHERE UPPER(status::text) NOT IN ('APPLIED', 'INTERVIEW', 'OFFER', 'REJECTED')
              AND LOWER(status::text) NOT IN ('applied', 'interview', 'offer', 'rejected', 'withdrawn')
        ) THEN
            RAISE EXCEPTION 'Preflight failed: existing applications rows contain unmappable status value';
        END IF;

        -- 4. Check for job owner mismatch
        IF EXISTS (
            SELECT 1
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.user_id != j.user_id
        ) THEN
            RAISE EXCEPTION 'Preflight failed: application user_id does not match job user_id owner';
        END IF;

        -- 5. Check for duplicate applications for same (user_id, job_id)
        IF EXISTS (
            SELECT user_id, job_id
            FROM applications
            GROUP BY user_id, job_id
            HAVING COUNT(*) > 1
        ) THEN
            RAISE EXCEPTION 'Preflight failed: duplicate applications found for (user_id, job_id)';
        END IF;

        -- 6. Check for embedded NULL elements in notes array
        IF EXISTS (
            SELECT 1 FROM applications
            WHERE notes IS NOT NULL AND array_position(notes, NULL) IS NOT NULL
        ) THEN
            RAISE EXCEPTION 'Preflight failed: notes array contains embedded NULL elements';
        END IF;
    END IF;
END $$;

-- Step 1: Ensure unique constraint on jobs(id, user_id)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'jobs_id_user_id_key'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT jobs_id_user_id_key UNIQUE (id, user_id);
    END IF;
END $$;

-- Step 2: Update applications table structure
-- Remove default on status column if it relies on old enum
ALTER TABLE applications ALTER COLUMN status DROP DEFAULT;

-- Change status column type to VARCHAR(20) converting to lowercase
ALTER TABLE applications ALTER COLUMN status TYPE VARCHAR(20) USING LOWER(status::text);

-- Drop old ApplicationStatus enum type if it exists
DROP TYPE IF EXISTS ApplicationStatus;

-- Add check constraint for valid lower-case statuses
ALTER TABLE applications ADD CONSTRAINT applications_status_check
    CHECK (status IN ('applied', 'interview', 'offer', 'rejected', 'withdrawn'));

ALTER TABLE applications ALTER COLUMN status SET NOT NULL;

-- Convert notes column from VARCHAR[] to TEXT (newline-separated) preserving NULL
ALTER TABLE applications ALTER COLUMN notes TYPE TEXT
    USING CASE
        WHEN notes IS NULL THEN NULL
        ELSE array_to_string(notes, E'\n')
    END;

-- Ensure created_at exists, initialize from applied_at for existing rows
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'applications' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE applications ADD COLUMN created_at TIMESTAMPTZ;
        UPDATE applications SET created_at = applied_at;
        ALTER TABLE applications ALTER COLUMN created_at SET NOT NULL;
        ALTER TABLE applications ALTER COLUMN created_at SET DEFAULT NOW();
    END IF;
END $$;

-- Ensure applied_at and updated_at are NOT NULL and default to NOW()
UPDATE applications SET updated_at = COALESCE(updated_at, created_at) WHERE updated_at IS NULL;
ALTER TABLE applications ALTER COLUMN applied_at SET NOT NULL;
ALTER TABLE applications ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE applications ALTER COLUMN updated_at SET DEFAULT NOW();

-- Step 3: Foreign key constraints
-- Drop existing foreign key constraint on job_id if present
DO $$
DECLARE
    fk_name text;
BEGIN
    FOR fk_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'applications'::regclass AND contype = 'f'
    LOOP
        EXECUTE 'ALTER TABLE applications DROP CONSTRAINT ' || quote_ident(fk_name);
    END LOOP;
END $$;

-- Re-add user FK with CASCADE
ALTER TABLE applications
    ADD CONSTRAINT fk_applications_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Add composite FK applications(job_id, user_id) -> jobs(id, user_id) with CASCADE
ALTER TABLE applications
    ADD CONSTRAINT fk_applications_job_user
    FOREIGN KEY (job_id, user_id) REFERENCES jobs(id, user_id) ON DELETE CASCADE;

-- Ensure UNIQUE(user_id, job_id)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'applications_user_id_job_id_key'
    ) THEN
        ALTER TABLE applications ADD CONSTRAINT applications_user_id_job_id_key UNIQUE (user_id, job_id);
    END IF;
END $$;

-- Step 4: Add index on user_id and status
CREATE INDEX IF NOT EXISTS idx_applications_user_status ON applications(user_id, status);
