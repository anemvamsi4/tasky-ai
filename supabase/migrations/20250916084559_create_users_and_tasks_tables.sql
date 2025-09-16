-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20)
);

-- Create tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    due_dt TIMESTAMP,
    working_dt TIMESTAMP,
    duration_mins INTEGER DEFAULT 0,
    priority SMALLINT DEFAULT 2,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT status_check CHECK (status IN ('pending', 'in_progress', 'completed', 'archived')),
    CONSTRAINT priority_check CHECK (priority BETWEEN 1 AND 3)
);

-- Create index on user_id for better query performance
CREATE INDEX idx_tasks_user_id ON tasks(user_id);

-- Create index on status for filtering
CREATE INDEX idx_tasks_status ON tasks(status);