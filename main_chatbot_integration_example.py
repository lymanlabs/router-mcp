#!/usr/bin/env python3
"""
Main Chatbot Integration Example
Shows exactly how to call Router MCP with user_id from your profiles table
"""

import asyncio
from typing import Optional

class MainChatbot:
    """Example of how your main chatbot should integrate with Router MCP"""
    
    def __init__(self):
        # In reality, you'd initialize your MCP client here
        # self.router_mcp_client = MCPClient("router_profiles_enhanced.py")
        pass
    
    async def handle_user_message(self, user_id: str, message: str) -> str:
        """
        Main chatbot message handler
        
        Args:
            user_id: UUID from auth.users (same as profiles.id)
            message: User's message
        """
        
        print(f"📨 Received message from user {user_id}: '{message}'")
        
        # Check if this is a commerce-related message
        if self.is_commerce_intent(message):
            print(f"🛒 Commerce intent detected → Routing to Router MCP")
            
            # Call Router MCP with user_id (this is the key part!)
            response = await self.call_router_mcp(user_id, message)
            
            print(f"✅ Got response from Router MCP")
            return response
        else:
            # Handle with main assistant
            print(f"💬 General intent → Handling with main assistant")
            return await self.main_assistant_response(message)
    
    def is_commerce_intent(self, message: str) -> bool:
        """Simple commerce detection"""
        commerce_keywords = [
            "pizza", "order", "buy", "purchase", "delivery", 
            "food", "ride", "uber", "dominos", "restaurant",
            "checkout", "pay", "cart"
        ]
        return any(keyword in message.lower() for keyword in commerce_keywords)
    
    async def call_router_mcp(self, user_id: str, message: str) -> str:
        """
        Call Router MCP - THIS IS THE KEY INTEGRATION POINT
        
        In your real implementation, this would be:
        
        response = await self.router_mcp_client.call_tool(
            "route_commerce_message_with_profiles",
            user_id=user_id,    # ← UUID from auth.users/profiles
            message=message
        )
        """
        
        # Simulated Router MCP call for demonstration
        print(f"🔄 [Simulated] Calling Router MCP:")
        print(f"   Tool: route_commerce_message_with_profiles")
        print(f"   user_id: {user_id}")
        print(f"   message: {message}")
        
        # In reality, this would be the actual MCP call
        # For demo, return a simulated response
        return f"[Router MCP Response] I'll help you with that! Let me connect you to the right service..."
    
    async def main_assistant_response(self, message: str) -> str:
        """Handle non-commerce messages with main assistant"""
        return f"I'm your main assistant. You said: '{message}'. How can I help?"

def show_integration_examples():
    """Show different integration scenarios"""
    
    print("🔧 MAIN CHATBOT INTEGRATION EXAMPLES")
    print("=" * 45)
    
    print("""
## 🎯 Key Integration Points

### 1. **User ID Source**
```python
# Your main chatbot gets user_id from authentication
user_id = current_user.id          # From Supabase auth.users
user_id = session.user.id          # From your auth system  
user_id = request.user.id          # From web framework
```

### 2. **Router MCP Call**
```python
# The critical call - pass user_id to Router MCP
response = await router_mcp_client.call_tool(
    "route_commerce_message_with_profiles",
    user_id=user_id,        # ← UUID that matches profiles.id
    message=user_message
)
```

### 3. **What Happens Behind the Scenes**
```
User ID: "550e8400-e29b-41d4-a716-446655440000"
↓
Router MCP queries: SELECT * FROM profiles WHERE id = '550e8400...'
↓
Profile found: {"full_name": "John Smith", "phone": "555-1234", ...}
↓
Enhanced handoff: "Customer name: John Smith. Phone: 555-1234. User said: 'I want pizza'"
↓
Claude gets personalized context + Domino's MCP tools
↓
Response: "Hi John! I'll help with pizza. Should I deliver to your usual address?"
```

## 🚀 Real Implementation Examples

### Flask/FastAPI Example:
```python
from flask import Flask, request, session
from your_mcp_client import MCPClient

app = Flask(__name__)
router_mcp = MCPClient("router_profiles_enhanced.py")

@app.route("/chat", methods=["POST"])
async def chat():
    user_id = session.user.id  # From your auth system
    message = request.json["message"]
    
    # Call Router MCP with user_id
    response = await router_mcp.call_tool(
        "route_commerce_message_with_profiles",
        user_id=str(user_id),  # Ensure it's a string
        message=message
    )
    
    return {"response": response}
```

### NextJS/React Example:
```javascript
// Frontend
const sendMessage = async (message) => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  return response.json();
};

// Backend API route
export default async function handler(req, res) {
  const { message } = req.body;
  const user = await getUser(req); // Your auth system
  
  // Call Router MCP
  const response = await routerMcpClient.callTool(
    "route_commerce_message_with_profiles",
    user.id,  // UUID from auth.users
    message
  );
  
  res.json({ response });
}
```

### Discord Bot Example:
```python
import discord
from discord.ext import commands

class CommerceBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!')
        self.router_mcp = MCPClient("router_profiles_enhanced.py")
    
    @commands.command()
    async def order(self, ctx, *, message):
        # Use Discord user ID as user_id
        user_id = str(ctx.author.id)
        
        response = await self.router_mcp.call_tool(
            "route_commerce_message_with_profiles", 
            user_id=user_id,
            message=message
        )
        
        await ctx.send(response)
```

## 🗃️ Database Schema Requirements

Your profiles table just needs to be accessible to Router MCP:

```sql
-- Your existing profiles table (no changes needed!)
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    full_name TEXT,
    email TEXT,
    phone TEXT,
    address JSONB,
    -- ... other fields you already have
);

-- Router MCP will query this automatically:
-- SELECT * FROM profiles WHERE id = $user_id
```

## ⚠️ Important Notes

### 1. **User ID Must Match**
```python
# ✅ CORRECT - Same UUID in both tables
auth.users.id     = "550e8400-e29b-41d4-a716-446655440000"
profiles.id       = "550e8400-e29b-41d4-a716-446655440000"  # Same!

# ❌ WRONG - Different IDs  
auth.users.id     = "550e8400-e29b-41d4-a716-446655440000"
profiles.user_id  = "12345"  # Different field/value
```

### 2. **Handle Missing Profiles Gracefully**
```python
# Router MCP handles this automatically:
if profile_exists:
    # Personalized: "Hi John! Pizza to 123 Main St?"
else:
    # Generic: "I'll help with pizza! What's your address?"
```

### 3. **Privacy & Security**
```python
# Router MCP only passes safe profile data to Claude:
safe_profile = {
    "name": profile.get("full_name"),
    "phone": profile.get("phone"), 
    "address": profile.get("address")
    # Payment methods are NOT passed to AI for security
}
```
""")

async def demo_conversation_flow():
    """Demo a complete conversation flow"""
    
    print("\n💬 DEMO CONVERSATION FLOW")
    print("=" * 30)
    
    chatbot = MainChatbot()
    
    # Simulate different users
    users = [
        {"id": "user-123-abc", "name": "Alice"},
        {"id": "user-456-def", "name": "Bob"}
    ]
    
    # Simulate conversation
    conversations = [
        ("user-123-abc", "Hello there!"),                    # General
        ("user-123-abc", "I want to order pizza"),           # Commerce → New session
        ("user-456-def", "I need an Uber ride"),            # Commerce → Different user  
        ("user-123-abc", "Make it large pepperoni"),         # Commerce → Continue Alice's session
        ("user-456-def", "To downtown please"),             # Commerce → Continue Bob's session
        ("user-123-abc", "What's the weather?"),            # General → Back to main assistant
    ]
    
    print("🎬 Simulating conversation flow:\n")
    
    for user_id, message in conversations:
        user_name = next(u["name"] for u in users if u["id"] == user_id)
        print(f"👤 {user_name} ({user_id}): '{message}'")
        
        response = await chatbot.handle_user_message(user_id, message)
        print(f"🤖 Response: {response}\n")
        
        await asyncio.sleep(0.5)  # Pause for readability

if __name__ == "__main__":
    show_integration_examples()
    
    print("\n" + "="*60)
    print("🎯 YOUR INTEGRATION CHECKLIST:")
    print("="*60)
    print("""
1. ✅ Use Router MCP: router_profiles_enhanced.py
2. ✅ Pass user_id from auth.users (matches profiles.id)  
3. ✅ Call: route_commerce_message_with_profiles(user_id, message)
4. ✅ Router automatically fetches profile and personalizes
5. ✅ Sessions persist across conversations
6. ✅ Multiple users are automatically isolated

🚀 That's it! Your Router MCP handles all the complexity!
""")
    
    # Run demo
    asyncio.run(demo_conversation_flow()) 