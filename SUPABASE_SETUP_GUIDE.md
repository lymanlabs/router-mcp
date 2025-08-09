# 🚀 Router MCP with Supabase - Complete Setup Guide

Your **original plan was correct!** Supabase is the perfect choice for this MCP Router. Here's how to get it running in 30 minutes.

## 📋 What You Already Have Ready

✅ **Schema designed** - `supabase_schema.sql` is complete  
✅ **Dependencies installed** - `supabase>=2.0.0` in requirements.txt  
✅ **Config template** - `config_template.env` has placeholders  
✅ **Implementation ready** - `router_supabase_mcp.py` is complete  

## 🏃‍♂️ Quick Setup (30 minutes)

### Step 1: Create Supabase Project (5 minutes)

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project" → Sign up/Sign in
3. Click "New Project"
4. Choose organization, enter:
   - **Name**: `router-mcp` (or whatever you prefer)  
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to you
5. Click "Create new project"
6. ⏳ Wait 2-3 minutes for project to initialize

### Step 2: Get Your Connection Details (2 minutes)

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (looks like `https://xxx.supabase.co`)
   - **anon/public key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

### Step 3: Set Up Database Schema (3 minutes)

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New query"
3. Copy the entire contents of `supabase_schema.sql` and paste it
4. Click "Run" (or Ctrl+Enter)
5. ✅ You should see "Success. No rows returned" - that's perfect!

### Step 4: Configure Environment (2 minutes)

Create a `.env` file in your project root:

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-key-here
```

Replace the placeholder values with your actual Supabase URL and key.

### Step 5: Test Your Setup (5 minutes)

```bash
# Activate your virtual environment
source venv/bin/activate

# Install dependencies (if not already done)
pip install -r requirements.txt

# Test the Supabase router
python router_supabase_mcp.py
```

You should see:
```
✅ Supabase connection successful
🚀 Supabase-backed Router MCP ready!
Sessions are persistent and multi-user ready! 🎉
```

## 🎯 Why Supabase is Perfect for You

| Feature | Supabase | Raw PostgreSQL | Redis |
|---------|----------|---------------|-------|
| **Setup Time** | 30 minutes | 2+ hours | 1 hour |
| **Persistence** | ✅ Always | ✅ Always | ⚠️ Memory-based |
| **Multi-user** | ✅ Built-in RLS | ❌ Custom auth | ❌ Custom auth |
| **Dashboard** | ✅ Beautiful UI | ❌ Command line | ❌ Command line |
| **Scaling** | ✅ Automatic | ❌ Manual | ❌ Manual |
| **Cost** | ✅ Free tier | 💰 Server costs | 💰 Memory costs |
| **Maintenance** | ✅ Zero | ❌ Full responsibility | ❌ Full responsibility |

## 🔄 How Sessions Work with Supabase

### 1. **User sends message to main chatbot**
```
User: "I want pizza from Dominos"
Main Chatbot: Detects commerce intent → calls Router MCP
```

### 2. **Router MCP checks Supabase**
```python
# router_supabase_mcp.py
session = await get_session(user_id="user123", service="dominos")
# → SELECT * FROM router_sessions WHERE user_id='user123' AND service='dominos'
```

### 3. **If no session exists, create one**
```python
# Insert new session into Supabase
session_data = {
    "session_id": "uuid-12345",
    "user_id": "user123", 
    "service": "dominos",
    "message_history": [{"role": "user", "content": "Handoff message..."}],
    "system_prompt": "You are a Domino's assistant...",
    "created_at": "2024-01-15T10:30:00Z"
}
supabase.table("router_sessions").insert(session_data).execute()
```

### 4. **Call Claude API with full context**
```python
# Get ENTIRE conversation from Supabase
response = anthropic_client.beta.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=session["message_history"],  # Full conversation!
    mcp_servers=[dominos_mcp_config]
)
```

### 5. **Update session in Supabase**
```python
# Add new messages to history
session["message_history"].append({"role": "assistant", "content": "I need your address..."})

# Update in Supabase
supabase.table("router_sessions").update({
    "message_history": session["message_history"],
    "last_active": datetime.now()
}).eq("session_id", session_id).execute()
```

### 6. **Server restart? No problem!**
```
Server restarts for deployment...
User: "Make it large pepperoni"
Router: Loads session from Supabase → Full context restored!
Claude: "Great! Adding large pepperoni to your order..."
```

## 🗃️ What's Stored in Supabase

Your `router_sessions` table will look like:

| session_id | user_id | service | message_history | last_active |
|------------|---------|---------|-----------------|-------------|
| uuid-123 | user123 | dominos | `[{"role":"user","content":"I want pizza"}...]` | 2024-01-15 10:45:23 |
| uuid-456 | user456 | uber | `[{"role":"user","content":"I need a ride"}...]` | 2024-01-15 10:43:12 |

The **`message_history`** column contains the **ENTIRE conversation** as JSON - this is what gets passed to Claude API!

## 🎉 Benefits You Get Immediately

1. **✅ Persistent sessions** - Survive server restarts, deployments, crashes
2. **✅ Multi-user ready** - Row Level Security isolates users automatically  
3. **✅ Real-time monitoring** - Watch sessions in Supabase dashboard
4. **✅ Automatic backups** - Supabase handles all database maintenance
5. **✅ Easy debugging** - See exact conversation history in admin panel
6. **✅ Scalable** - Handles thousands of concurrent users
7. **✅ Free tier** - 50,000 rows, 500MB storage, 2GB bandwidth

## 🔧 Advanced Configuration (Optional)

### Enable Row Level Security Policies

Your schema already includes RLS policies, but to enable user authentication:

```sql
-- In Supabase SQL Editor, these are already in supabase_schema.sql:

-- Enable RLS
ALTER TABLE router_sessions ENABLE ROW LEVEL SECURITY;

-- Users can only see their own sessions
CREATE POLICY "Users can only access their own sessions" 
ON router_sessions FOR ALL USING (auth.uid()::text = user_id);
```

### Add Session Cleanup (Automatic)

```sql
-- Clean up sessions older than 7 days (already in schema)
CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM router_sessions 
    WHERE last_active < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup to run daily at 2 AM
SELECT cron.schedule('cleanup-old-sessions', '0 2 * * *', 'SELECT cleanup_old_sessions();');
```

## 🚀 Production Deployment

When you're ready for production:

1. **Upgrade Supabase plan** if needed (free tier is quite generous)
2. **Add connection pooling** (Supabase handles this automatically)
3. **Enable database backups** (enabled by default in Supabase)
4. **Monitor usage** in Supabase dashboard
5. **Set up alerts** for high usage

## 🔄 Migration Path (Future)

```
Phase 1: Supabase (NOW) → Get to market fast ✅
Phase 2: Add Redis caching → Handle more concurrent users  
Phase 3: Self-hosted PostgreSQL → Full control (if needed)
```

Supabase uses PostgreSQL under the hood, so migration is straightforward if you ever need it.

## 💡 Next Steps

1. **✅ Set up Supabase** (follow steps above)
2. **✅ Test with `router_supabase_mcp.py`** 
3. **🚀 Deploy your Router MCP**
4. **📊 Monitor sessions** in Supabase dashboard
5. **🎉 Enjoy persistent, multi-user sessions!**

---

## 🎯 Key Insight

**Your original Supabase plan was perfect!** 

- ✅ All the infrastructure is ready
- ✅ Schema is designed and tested  
- ✅ Implementation is complete
- ✅ You can be running in 30 minutes

**Database storage is essential** - without it, users lose their pizza orders every time your server restarts! 🍕 