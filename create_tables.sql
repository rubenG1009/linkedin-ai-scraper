-- Create the job_schedules table
CREATE TABLE IF NOT EXISTS job_schedules (
    job_name VARCHAR(100) PRIMARY KEY,
    cron_expression VARCHAR(100) NOT NULL,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert a test record
INSERT INTO job_schedules (
    job_name,
    cron_expression,
    next_run_at,
    enabled
) VALUES (
    'linkedin_recruiter_search',
    '0 9 * * 1-5',  -- Every weekday at 9 AM
    CURRENT_TIMESTAMP + INTERVAL '1 hour',
    true
) ON CONFLICT (job_name) DO NOTHING;
