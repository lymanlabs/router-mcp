-- Router Sessions table for storing background chat sessions
CREATE TABLE router_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    service VARCHAR(50) NOT NULL,
    system_prompt TEXT NOT NULL,
    message_history JSONB NOT NULL DEFAULT '[]',
    available_tools TEXT[] NOT NULL DEFAULT '{}',
    context JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_router_sessions_user_id ON router_sessions(user_id);
CREATE INDEX idx_router_sessions_service ON router_sessions(service);
CREATE INDEX idx_router_sessions_last_active ON router_sessions(last_active);
CREATE INDEX idx_router_sessions_user_service ON router_sessions(user_id, service);

-- Create index for session lookup
CREATE INDEX idx_router_sessions_session_id ON router_sessions(session_id);

-- Enable Row Level Security (RLS)
ALTER TABLE router_sessions ENABLE ROW LEVEL SECURITY;

-- Create policy for users to only access their own sessions
CREATE POLICY "Users can only access their own sessions" ON router_sessions
    FOR ALL USING (auth.uid()::text = user_id);

-- Create policy for service access (if needed for service-specific queries)
CREATE POLICY "Allow service-specific access" ON router_sessions
    FOR SELECT USING (true); -- Adjust based on your security requirements

-- Function to clean up old sessions (optional, for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM router_sessions 
    WHERE last_active < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run cleanup (optional)
-- Note: This requires the pg_cron extension to be enabled
-- SELECT cron.schedule('cleanup-old-sessions', '0 2 * * *', 'SELECT cleanup_old_sessions();');

-- Add some helpful comments
COMMENT ON TABLE router_sessions IS 'Stores background chat sessions for the MCP router';
COMMENT ON COLUMN router_sessions.session_id IS 'Unique identifier for the session (user_id_service_timestamp)';
COMMENT ON COLUMN router_sessions.user_id IS 'References the authenticated user ID from Supabase auth';
COMMENT ON COLUMN router_sessions.service IS 'Which MCP service this session is for (dominos, uber, doordash, etc.)';
COMMENT ON COLUMN router_sessions.system_prompt IS 'Service-specific AI behavior instructions';
COMMENT ON COLUMN router_sessions.message_history IS 'Complete conversation stored as JSON array';
COMMENT ON COLUMN router_sessions.available_tools IS 'Array of MCP tools available for this service';
COMMENT ON COLUMN router_sessions.context IS 'User preferences and session-specific data';
COMMENT ON COLUMN router_sessions.last_active IS 'Timestamp of last activity for session management'; 