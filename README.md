# 🔄 Router MCP - Commerce Service Router

**Intelligent proxy that routes commerce conversations to specialized service MCPs with automatic session management and profile integration.**

## 🎯 What This Does

Your main chatbot calls Router MCP → Router creates background Claude sessions with specialized MCPs (Domino's, Uber, etc.) → Returns personalized responses using user profile data.

## 📁 Repository Structure

```
router_mcp/
├── 🚀 CORE FILES
│   ├── router_profiles_enhanced.py      # Main Router MCP implementation
│   ├── supabase_schema.sql             # Database schema for sessions
│   ├── requirements.txt                # Dependencies
│   └── config_template.env             # Environment configuration
│
├── 📚 DOCUMENTATION  
│   ├── FINAL_ROUTER_SUMMARY.md         # Quick implementation summary
│   ├── SUPABASE_SETUP_GUIDE.md         # Complete setup guide
│   └── main_chatbot_integration_example.py  # Integration examples
│
└── venv/                               # Virtual environment
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config_template.env .env
# Edit .env with your Supabase URL, KEY, and Anthropic API key
```

### 2. Setup Database
```bash
# Run supabase_schema.sql in your Supabase SQL Editor
# This creates the router_sessions table
```

### 3. Use Router MCP
```python
# In your main chatbot
response = await router_mcp_client.call_tool(
    "route_commerce_message_with_profiles",
    user_id=current_user.id,    # UUID from auth.users
    message=user_message
)
```

## 🔧 How It Works

1. **User sends message** → Your main chatbot
2. **Main chatbot passes UID + message** → Router MCP
3. **Router MCP**:
   - Queries your `profiles` table for user info
   - Creates/continues session for user+service
   - Calls Claude API with service MCP + profile context
4. **Returns personalized response** → Your main chatbot

## 🎉 What You Get

**Without Router MCP:**
```
User: "I want pizza"
🤖: "What's your address? Phone? Payment method?"
```

**With Router MCP:**
```
User: "I want pizza"  
🤖: "Hi John! Large pepperoni to 123 Main St? Charging your Visa ending in 1234. Total: $15.99?"
```

## 🗃️ Key Features

✅ **UID-based session management** - Each user gets isolated conversations  
✅ **Automatic profile integration** - Uses your existing Supabase profiles table  
✅ **Persistent sessions** - Conversations survive server restarts  
✅ **Multi-service support** - Domino's, Uber, DoorDash (easily extensible)  
✅ **Personalized responses** - Name, address, payment info automatically included  

## 📊 Database Requirements

Your existing Supabase setup with `profiles` table - **no changes needed!**

```sql
-- Your existing profiles table (Router MCP queries this automatically)
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    full_name TEXT,
    email TEXT, 
    phone TEXT,
    address JSONB,
    -- ... other fields you have
);
```

## 🔑 Environment Variables

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
ANTHROPIC_API_KEY=sk-ant-api03-...
```

## 🚀 Running the Router

```bash
python router_profiles_enhanced.py
```

## 📖 Documentation

- **`FINAL_ROUTER_SUMMARY.md`** - Quick overview and key concepts
- **`SUPABASE_SETUP_GUIDE.md`** - Complete setup walkthrough  
- **`main_chatbot_integration_example.py`** - Integration examples for different frameworks

## �� Main Integration

```python
# This is all you need in your main chatbot:
class MainChatbot:
    def __init__(self):
        self.router_mcp = MCPClient("router_profiles_enhanced.py")
    
    async def handle_message(self, user_id: str, message: str):
        if self.is_commerce(message):
            return await self.router_mcp.call_tool(
                "route_commerce_message_with_profiles",
                user_id=user_id,  # ← UID from auth.users
                message=message
            )
        else:
            return await self.general_assistant(message)
```

## 🔄 Architecture

```
Main Chatbot → Router MCP → Background Claude + Service MCP → Response

User Profile (Supabase) ↗        ↘ Session Storage (Supabase)
```

## ✅ Ready to Use

This repository contains everything you need for a production-ready Router MCP with:
- Session management
- Profile integration  
- Multi-user isolation
- Persistent conversations
- Personalized commerce experiences

Just set up Supabase, configure your environment, and start routing! 🎉 