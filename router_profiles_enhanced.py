#!/usr/bin/env python3
"""
Router MCP with Profiles Integration - Ready to Use
Connects to your existing Supabase profiles table
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP
from anthropic import Anthropic
from supabase import create_client, Client

# Initialize FastMCP server
mcp = FastMCP("commerce-router-profiles")

# Initialize Claude client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    print("❌ SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

# Service configurations
SERVICE_CONFIGS = {
    "dominos": {
        "keywords": ["pizza", "dominos", "domino's", "order food", "hungry", "pepperoni", "cheese", "delivery"],
        "mcp_config": {
            "type": "url", 
            "url": "https://server.smithery.ai/@mdwoicke/dominos-mcp/mcp?api_key=debf2e51-700f-48bf-a182-f988d520fb93&profile=yappy-ferret-cadRN3",
            "name": "dominos-mcp"
        },
        "description": "Domino's Pizza ordering service",
        "system_prompt": "You are a helpful Domino's Pizza assistant. Help users find stores, browse menus, create orders, and complete purchases. Always ask for required information like address, contact details, and payment when needed."
    },
    "opentable": {
        "keywords": ["restaurant", "reservation", "book table", "dinner", "lunch", "opentable", "reserve", "table for", "dining", "eat out"],
        "mcp_config": {
            "type": "url",
            "url": "https://lymanlabs--opentable-mcp-server-serve.modal.run/mcp",
            "name": "opentable-mcp"
        },
        "description": "OpenTable restaurant reservation service", 
        "system_prompt": """You are a helpful OpenTable restaurant reservation assistant. Help users find restaurants, check availability, and make reservations. Always ask for required information like location, date, time, party size, and special requests when needed. You can search restaurants, check availability, book reservations, and manage existing reservations.

OPENTABLE MCP USAGE GUIDE:

For restaurant reservations, follow this flow:

1. SEARCH FIRST: Always start with search_restaurants(user_id, location, ...)
   - This automatically handles user registration if needed
   - Don't call ensure_opentable_user() separately - it's redundant
   - Pass user_id as first parameter always

2. SHOW OPTIONS: Present restaurant results to user
   - Show restaurant names, cuisines, locations, ratings
   - IMPORTANT: Keep track of each restaurant's restaurant_id from the search results
   - Let user pick their preferred restaurant

3. CHECK AVAILABILITY: When user picks a restaurant, call get_availability(user_id, restaurant_id, ...)
   - CRITICAL: Use the exact restaurant_id from the search results in step 1
   - NEVER search again by restaurant name - always use the restaurant_id
   - Specify party_size, days to search, time preferences

4. BOOK RESERVATION: When user confirms, call book_reservation(user_id, ...) with all the slot details
   - Use exact slot_hash, date_time, availability_token from availability results
   - Include all required parameters: restaurant_id, party_size, location

5. MANAGE EXISTING: Use list_reservations(user_id) or cancel_reservation(user_id, ...) as needed

IMPORTANT: 
- Always pass the user_id as the first parameter to ALL OpenTable functions
- The search_restaurants() function handles account creation automatically
- All functions return success/error status - check before proceeding
- Never skip the availability check - booking requires availability tokens
- CRITICAL: Once you have a restaurant_id from search results, ALWAYS use that exact restaurant_id for get_availability() - NEVER search again by restaurant name

EXAMPLE FLOW:
User: "Book sushi in NYC for 4 people tonight"
1. search_restaurants(user_id, "New York", "sushi", party_size=4)
2. [Show results with restaurant names and IDs to user]
3. User picks "Sushi Zen" → Use the restaurant_id from step 1 results (e.g. "rest_12345")
4. get_availability(user_id, "rest_12345", party_size=4) ← Use restaurant_id, NOT restaurant name
5. [Show time slots to user]
6. book_reservation(user_id, "rest_12345", slot_hash, datetime, token, 4, "New York")

ERROR HANDLING:
- If search fails, suggest different location or cuisine
- If no availability, suggest different dates/times
- If booking fails, check if slot is still available
- Always inform user of next steps if something fails"""
    },
    "uber": {
        "keywords": ["uber", "ride", "taxi", "car", "transport", "pickup", "drop off", "book ride", "schedule ride", "transportation", "driver", "trip", "travel", "airport", "commute"],
        "mcp_config": {
            "type": "url",
            "url": "https://usman-hanif--uber-central-public-mcp-serve.modal.run/mcp",
            "name": "uber-central-mcp"
        },
        "description": "Uber ride booking and management service",
        "system_prompt": """You are a helpful Uber ride booking assistant. Help users book rides, get estimates, and manage transportation needs. Always collect required information like pickup/dropoff addresses, rider name, and phone number.

UBER MCP USAGE GUIDE:

For ride bookings, follow this flow:

1. INITIALIZE FIRST: Always start with initialize_user(user_id, name, email)
   - This automatically handles client account creation if needed
   - Pass user_id as first parameter always
   - Returns client_id for all subsequent operations

2. GET ESTIMATES: Call get_estimates(client_id, pickup_address, dropoff_address, capacity)
   - Show pricing and vehicle options to user
   - Let user choose vehicle type if preferences given

3. BOOK RIDE: Collect required info then call:
   - book_ride() for immediate rides
   - schedule_ride() for future rides (with pickup_time in ISO format)
   - Required: pickup_address, dropoff_address, rider_name, rider_phone

4. MANAGE RIDES: Use get_ride_status(ride_id) or cancel_ride(ride_id) as needed

IMPORTANT:
- Always pass user_id to initialize_user first, then use returned client_id
- Never ask user for their user_id - it's in system context
- Be specific with addresses - "123 Main St, San Francisco, CA" not "downtown"
- Rider name/phone can be different from user (booking for others)
- Confirm all details before booking

EXAMPLE FLOW:
User: "Book me an Uber to the airport"
1. initialize_user(user_id, user_name, user_email)
2. Ask pickup location
3. get_estimates(client_id, pickup, "Airport", 1)
4. book_ride(client_id, pickup, airport, rider_name, rider_phone)

ERROR HANDLING:
- If client_id errors: Re-run initialize_user
- If booking fails: Show error and suggest alternatives
- Always provide ride_id for tracking after successful bookings"""
    }
}

def classify_intent(message: str) -> str:
    """Classify user intent based on keywords"""
    message_lower = message.lower()
    
    for service, config in SERVICE_CONFIGS.items():
        for keyword in config["keywords"]:
            if keyword in message_lower:
                return service
    
    return "general"

async def get_user_profile(user_id: str) -> Optional[Dict]:
    """Fetch user profile from your existing profiles table"""
    try:
        result = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        if result.data:
            profile = result.data[0]
            print(f"✅ Found profile for user {user_id}: {profile.get('full_name', 'No name')}")
            return profile
        else:
            print(f"📝 No profile found for user {user_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching profile: {e}")
        return None

async def create_session_with_profile(user_id: str, service: str, initial_message: str) -> Optional[Dict]:
    """Create new session in Supabase with profile data"""
    
    # Get user profile from your existing table
    profile = await get_user_profile(user_id)
    
    session_id = str(uuid.uuid4())
    service_config = SERVICE_CONFIGS[service]
    
    # Create enhanced handoff message with profile context
    if profile:
        profile_context = ""
        if profile.get("full_name"):
            profile_context += f"Customer name: {profile['full_name']}. "
        if profile.get("phone"):
            profile_context += f"Phone: {profile['phone']}. "
        if profile.get("address"):
            # Handle both string and JSON address formats
            address = profile['address']
            if isinstance(address, dict):
                address_str = f"{address.get('street', '')}, {address.get('city', '')}"
            else:
                address_str = str(address)
            profile_context += f"Address: {address_str}. "
        
        handoff_message = f"""I'm connecting you with {service_config['description']}. 
{profile_context}
The user said: '{initial_message}' - please help them with their request."""
    else:
        # Fallback without profile
        handoff_message = f"I'm connecting you with {service_config['description']}. The user said: '{initial_message}' - please help them with their request."
    
    # Session data with profile stored in context
    session_data = {
        "session_id": session_id,
        "user_id": user_id,
        "service": service,
        "system_prompt": service_config["system_prompt"],
        "message_history": [{"role": "user", "content": handoff_message}],
        "available_tools": [],
        "context": {
            "service_config": service_config,
            "user_profile": profile  # Store profile for later use
        },
        "created_at": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat()
    }
    
    try:
        print(f"🔄 Attempting to create {service} session in Supabase for user {user_id}")
        result = supabase.table("router_sessions").insert(session_data).execute()
        
        if result.data:
            print(f"✅ Created new {service} session with profile for user {user_id}")
            return result.data[0]
        else:
            print(f"❌ Failed to create session in Supabase - no data returned")
            print(f"📝 Result: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Supabase error creating session: {type(e).__name__}: {e}")
        print(f"📝 Session data attempted: {session_data}")
        return None

async def get_session(user_id: str, service: str) -> Optional[Dict]:
    """Get active session from Supabase"""
    try:
        cutoff_time = (datetime.now() - timedelta(minutes=30)).isoformat()
        
        result = supabase.table("router_sessions").select("*").eq(
            "user_id", user_id
        ).eq("service", service).gt(
            "last_active", cutoff_time
        ).execute()
        
        if result.data:
            session = result.data[0]
            print(f"✅ Found existing {service} session for user {user_id}")
            return session
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error getting session: {e}")
        return None

async def get_any_active_session(user_id: str) -> Optional[Dict]:
    """Get any active session for a user (regardless of service)"""
    try:
        cutoff_time = (datetime.now() - timedelta(minutes=30)).isoformat()
        
        result = supabase.table("router_sessions").select("*").eq(
            "user_id", user_id
        ).gt("last_active", cutoff_time).execute()
        
        if result.data:
            session = result.data[0]  # Get the most recent one
            print(f"✅ Found existing {session['service']} session for user {user_id}")
            return session
        else:
            print(f"📝 No active sessions found for user {user_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting any active session: {e}")
        return None

async def update_session(session: Dict) -> bool:
    """Update session in Supabase"""
    try:
        session["last_active"] = datetime.now().isoformat()
        
        result = supabase.table("router_sessions").update({
            "message_history": session["message_history"],
            "last_active": session["last_active"],
            "context": session.get("context", {})
        }).eq("session_id", session["session_id"]).execute()
        
        return bool(result.data)
        
    except Exception as e:
        print(f"❌ Error updating session: {e}")
        return False

async def call_background_claude_with_profile(session: Dict, new_message: str) -> str:
    """Call Claude API with profile-enhanced system prompt"""
    try:
        service_config = session["context"]["service_config"]
        profile = session["context"].get("user_profile")
        
        # Add new message to history
        if new_message:
            session["message_history"].append({"role": "user", "content": new_message})
        
        # Enhanced system prompt with profile context
        enhanced_system_prompt = service_config["system_prompt"]
        
        # Add concise response style instruction to all prompts
        enhanced_system_prompt += """

RESPONSE STYLE:
- Be clear, concise, and direct
- Avoid unnecessary explanations or verbose descriptions  
- Get straight to the point
- Only provide essential information needed for the user's request
"""
        
        if profile:
            enhanced_system_prompt += f"""

CUSTOMER PROFILE:
- User ID: {session.get('user_id', 'Not provided')}
- Name: {profile.get('full_name', 'Not provided')}
- Phone: {profile.get('phone', 'Not provided')}
- Email: {profile.get('email', 'Not provided')}
- Address: {profile.get('address', 'Not provided')}

Use this profile information to provide personalized service. The User ID can be used to store/retrieve service-specific authentication tokens or preferences if your MCP supports it. If the customer needs to place an order, you already have their contact information and can use it to streamline the process.
"""
        
        # Call Claude with service MCP attached
        if "mcp_config" in service_config:
            try:
                print(f"🤖 CLAUDE+{session['service'].upper()}: calling...")
                response = anthropic_client.beta.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=1500,
                    messages=session["message_history"],
                    mcp_servers=[service_config["mcp_config"]],
                    betas=["mcp-client-2025-04-04"],  # Updated beta version
                    system=enhanced_system_prompt
                )
                print(f"✅ CLAUDE+{session['service'].upper()}: success")
            except Exception as mcp_error:
                print(f"❌ CLAUDE+{session['service'].upper()}: {type(mcp_error).__name__}")
                # Fallback to regular Claude call without MCP
                response = anthropic_client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=1000,
                    messages=session["message_history"],
                    system=f"{enhanced_system_prompt}\n\nNote: I don't have access to external tools right now, but I can still help you with general information about {session['service']}."
                )
        else:
            response = anthropic_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                messages=session["message_history"],
                system=enhanced_system_prompt
            )
        
        # Process all content blocks (text, tool_use, tool_result)
        assistant_response = ""
        tool_results = []
        
        for content_block in response.content:
            if hasattr(content_block, 'text') and content_block.text:
                assistant_response += content_block.text
            elif hasattr(content_block, 'type') and content_block.type == 'tool_result':
                # Extract actual results from OpenTable/Dominos MCP
                if hasattr(content_block, 'content') and content_block.content:
                    tool_result_text = content_block.content[0].text if content_block.content else ""
                    tool_results.append(tool_result_text)
                    assistant_response += f"\n\n{tool_result_text}"
        
        # If no meaningful response, provide fallback
        if not assistant_response.strip():
            assistant_response = f"I received a response from {session['service']} but couldn't process it properly."
        
        print(f"🔧 TOOLS: {len(tool_results)} results, {len(assistant_response)} chars")
        
        # Add response to history and update session
        session["message_history"].append({"role": "assistant", "content": assistant_response})
        await update_session(session)
        
        return assistant_response
        
    except Exception as e:
        error_details = f"{type(e).__name__}: {str(e)}"
        print(f"❌ Error in call_background_claude_with_profile: {error_details}")
        return f"Sorry, I encountered an error with {session['service']}: {error_details}"

@mcp.tool()
async def route_commerce_message_with_profiles(
    user_id: str,
    message: str,
    force_service: Optional[str] = None,
    force_new_session: Optional[bool] = False
) -> str:
    """
    Route commerce messages with automatic profile integration.
    
    Args:
        user_id: UUID from auth.users (references your profiles table)
        message: The user's message
        force_service: Optional - force routing to specific service
        force_new_session: Optional - force starting a new session even if one exists
    
    Returns:
        Personalized response from the specialized service
    """
    
    # 📥 ROUTER INPUT
    print(f"📥 IN: user={user_id[:8]}... msg='{message[:50]}{'...' if len(message) > 50 else ''}'")
    
    # Check if user has an active session first
    existing_session = await get_any_active_session(user_id)
    
    if force_new_session:
        # Force new session - clean up any existing ones
        print(f"🔄 Force new session requested - cleaning up existing sessions")
        await cleanup_expired_sessions()  # Clean up old session
        existing_session = None
    
    if existing_session:
        # Check if message contains keywords for a DIFFERENT service
        intended_service = classify_intent(message)
        
        if intended_service != "general" and intended_service != existing_session['service']:
            # User explicitly mentioned a different service - switch!
            print(f"🔄 SWITCH: {existing_session['service']} → {intended_service}")
            await cleanup_expired_sessions()  # Clean up old session
            session = None
            service = intended_service
        else:
            # Continue with existing session (even if intent is "general")
            print(f"✅ CONTINUE: {existing_session['service']} session")
            session = existing_session
            service = existing_session['service']
    else:
        # No active session - determine service from intent
        if force_service and force_service in SERVICE_CONFIGS:
            intended_service = force_service
        else:
            intended_service = classify_intent(message)
        
        if intended_service == "general":
            return "I specialize in commerce services like ordering food, booking rides, etc. For general questions, please use the main assistant."
        
        if intended_service not in SERVICE_CONFIGS:
            available = ", ".join(SERVICE_CONFIGS.keys())
            return f"Sorry, I don't support '{intended_service}' yet. Available services: {available}"
        
        # No existing session - start new one
        print(f"🆕 NEW: {intended_service} session")
        session = None
        service = intended_service
    
    if session is None:
        # Create new session with profile integration
        session = await create_session_with_profile(user_id, service, message)
        if not session:
            print(f"❌ FAILED: {service} session creation")
            return f"Sorry, I couldn't create a session for {service}. Please check your database connection and try again."
        
        print(f"✅ CREATED: {service} session")
        # First call uses the enhanced handoff message
        response = await call_background_claude_with_profile(session, "")
    else:
        # Continue existing session
        response = await call_background_claude_with_profile(session, message)
    
    # 📤 ROUTER OUTPUT
    print(f"📤 OUT: {len(response)} chars → '{response[:100]}{'...' if len(response) > 100 else ''}'")
    
    return response

@mcp.tool()
async def get_user_profile_info(user_id: str) -> str:
    """Get user profile information for debugging/verification"""
    profile = await get_user_profile(user_id)
    
    if profile:
        safe_info = {
            "name": profile.get("full_name"),
            "email": profile.get("email"),
            "has_phone": bool(profile.get("phone")),
            "has_address": bool(profile.get("address")),
            "profile_id": profile.get("id")
        }
        return f"Profile found: {json.dumps(safe_info, indent=2)}"
    else:
        return f"No profile found for user {user_id}"

# Test connections on startup
def test_connections():
    """Test Supabase connections"""
    try:
        # Test router_sessions table
        supabase.table("router_sessions").select("count").execute()
        print("✅ router_sessions table accessible")
        
        # Test profiles table  
        supabase.table("profiles").select("count").execute()
        print("✅ profiles table accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure both router_sessions and profiles tables exist in Supabase")
        return False

# Run the server
if __name__ == "__main__":
    print("🔄 Starting Commerce Router MCP with Profiles Integration")
    print("=" * 60)
    
    if test_connections():
        print("\nAvailable services:")
        for name, config in SERVICE_CONFIGS.items():
            status = "✅" if "mcp_config" in config else "🚧"
            print(f"  {status} {name}: {config['description']}")
        
        print(f"\n🚀 Profile-integrated Router MCP ready!")
        print(f"✅ Sessions persist across restarts")
        print(f"✅ Multi-user isolation with RLS")  
        print(f"✅ Automatic profile integration")
        print(f"📞 Main tool: route_commerce_message_with_profiles(user_id, message)")
        print(f"📞 Debug tool: get_user_profile_info(user_id)")
        
        # Start the MCP server
        import asyncio
        asyncio.run(mcp.run())
    else:
        print("❌ Cannot start server without database access")
        exit(1) 