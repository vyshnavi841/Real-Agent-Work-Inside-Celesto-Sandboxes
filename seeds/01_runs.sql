-- Initialize run ledger schema and insert baseline seed
CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR(255) PRIMARY KEY,
    sandbox_name VARCHAR(255) NOT NULL,
    problem_id VARCHAR(255) NOT NULL,
    state VARCHAR(50) NOT NULL,
    execution_target VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed row required by evaluation contract:
-- Sandbox name sbx-seeddemo1, state deleted, execution target celesto_sandbox
-- Re-running the SQL does not duplicate it.
INSERT INTO runs (run_id, sandbox_name, problem_id, state, execution_target)
VALUES (
    'run-seed-001',
    'sbx-seeddemo1',
    'issue-repro-seed-task',
    'deleted',
    'celesto_sandbox'
)
ON CONFLICT (run_id) DO NOTHING;
