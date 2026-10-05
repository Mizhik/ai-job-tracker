-- Rollback 005: Applications Stage 08
-- Preflight data safety checks
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'applications') THEN
        -- 1. Check for status 'withdrawn'
        IF EXISTS (
            SELECT 1 FROM applications WHERE status = 'withdrawn'
        ) THEN
            RAISE EXCEPTION 'Rollback aborted: applications contains withdrawn status which cannot be converted to legacy ApplicationStatus enum';
        END IF;

        -- 2. Check for multiline notes or empty string notes that cannot be safely rolled back
        IF EXISTS (
            SELECT 1 FROM applications WHERE notes IS NOT NULL AND (POSITION(E'\n' IN notes) > 0 OR notes = '')
        ) THEN
            RAISE EXCEPTION 'Rollback aborted: applications contains multiline or empty-string notes which cannot be converted back to VARCHAR[] losslessly';
        END IF;
    END IF;
END $$;

-- Drop new index
DROP INDEX IF EXISTS idx_applications_user_status;

-- Drop composite foreign key and user foreign key
ALTER TABLE applications DROP CONSTRAINT IF EXISTS fk_applications_job_user;
ALTER TABLE applications DROP CONSTRAINT IF EXISTS fk_applications_user;

-- Re-add standard foreign keys
ALTER TABLE applications
    ADD CONSTRAINT applications_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE applications
    ADD CONSTRAINT applications_job_id_fkey
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;

-- Drop jobs unique constraint if created
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_id_user_id_key;

-- Re-create legacy ApplicationStatus enum type if not present
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'applicationstatus') THEN
        CREATE TYPE ApplicationStatus AS ENUM ('NEW', 'APPLIED', 'INTERVIEW', 'OFFER', 'REJECTED');
    END IF;
END $$;

-- Drop status check constraint
ALTER TABLE applications DROP CONSTRAINT IF EXISTS applications_status_check;

-- Convert status column back to uppercase enum
ALTER TABLE applications ALTER COLUMN status TYPE ApplicationStatus USING UPPER(status)::ApplicationStatus;
ALTER TABLE applications ALTER COLUMN status SET DEFAULT 'NEW'::ApplicationStatus;

-- Convert notes column back to VARCHAR[]
ALTER TABLE applications ALTER COLUMN notes TYPE VARCHAR[]
    USING CASE
        WHEN notes IS NULL THEN NULL
        ELSE string_to_array(notes, E'\n')
    END;

-- Remove created_at column added by migration 005 to restore pre-005 schema fidelity
ALTER TABLE applications DROP COLUMN IF EXISTS created_at;

-- Restore nullability state for user_id, job_id, applied_at and updated_at per pre-005 schema
ALTER TABLE applications ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE applications ALTER COLUMN job_id DROP NOT NULL;
ALTER TABLE applications ALTER COLUMN applied_at DROP NOT NULL;
ALTER TABLE applications ALTER COLUMN updated_at DROP NOT NULL;
