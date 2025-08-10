"""
Enhanced MCP Server with Comprehensive Request Logging
Add this logging to your existing MCP server
"""

import modal
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import time
from datetime import datetime

app = modal.App("commerce-router-mcp-http")

# Your existing image setup...
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install([
        "fastapi[standard]",
        "mcp>=1.2.0",
        "anthropic>=0.34.0", 
        "supabase>=2.0.0",
        "httpx>=0.25.0",
        "python-dotenv>=1.0.0"
    ])
    .add_local_file("router_profiles_enhanced.py", remote_path="/app/router_profiles_enhanced.py")
)

fastapi_app = FastAPI()

# Enhanced logging function
def log_request_details(request: Request, method: str = None, body: dict = None):
    """Comprehensive request logging"""
    timestamp = datetime.now().isoformat()
    
    print("=" * 80)
    print(f"🔍 INCOMING REQUEST @ {timestamp}")
    print("=" * 80)
    
    # Basic request info
    print(f"📍 Method: {request.method}")
    print(f"📍 URL: {str(request.url)}")
    print(f"📍 Path: {request.url.path}")
    print(f"📍 Query Params: {dict(request.query_params)}")
    
    # Headers
    print(f"📋 Headers:")
    for name, value in request.headers.items():
        # Don't log sensitive auth headers in full
        if 'authorization' in name.lower() or 'key' in name.lower():
            print(f"    {name}: [REDACTED]")
        else:
            print(f"    {name}: {value}")
    
    # Client info
    client_host = request.client.host if request.client else "unknown"
    client_port = request.client.port if request.client else "unknown"
    print(f"🌐 Client: {client_host}:{client_port}")
    
    # User agent analysis
    user_agent = request.headers.get("user-agent", "No User-Agent")
    print(f"🤖 User-Agent: {user_agent}")
    
    # Determine request source
    if "anthropic" in user_agent.lower():
        print("🎯 REQUEST SOURCE: Anthropic's MCP Client")
    elif "curl" in user_agent.lower():
        print("🎯 REQUEST SOURCE: cURL (likely testing)")
    elif "python" in user_agent.lower():
        print("🎯 REQUEST SOURCE: Python script")
    elif "mozilla" in user_agent.lower() or "chrome" in user_agent.lower():
        print("🎯 REQUEST SOURCE: Web Browser")
    else:
        print("🎯 REQUEST SOURCE: Unknown")
    
    # MCP protocol info (if POST with body)
    if body:
        print(f"📦 MCP Method: {method}")
        print(f"📦 MCP Params: {body.get('params', {})}")
        print(f"📦 MCP ID: {body.get('id', 'None')}")
        print(f"📦 Full Body: {json.dumps(body, indent=2)}")
    
    print("=" * 80)

@fastapi_app.middleware("http")
async def log_all_requests(request: Request, call_next):
    """Middleware to log every single request"""
    start_time = time.time()
    
    # Log the incoming request
    print(f"\n🚨 REQUEST INTERCEPTED: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log the response
    duration = (time.time() - start_time) * 1000
    print(f"✅ RESPONSE: {response.status_code} (took {duration:.1f}ms)")
    
    return response

@fastapi_app.post("/mcp")
async def mcp_handler(request: Request):
    """Enhanced MCP endpoint with detailed logging"""
    try:
        import sys
        sys.path.append("/app")
        from router_profiles_enhanced import route_commerce_message_with_profiles
        
        # Handle empty body requests (third request from Anthropic)
        try:
            body = await request.json()
            method = body.get("method")
        except Exception as e:
            print("🚨 EMPTY BODY REQUEST DETECTED!")
            print(f"🔧 JSON parse error: {str(e)}")
            print("🔧 Returning HTTP 202 Accepted with empty body")
            return JSONResponse(content="", status_code=202)
        
        # Log comprehensive request details
        log_request_details(request, method, body)
        
        # Handle MCP protocol messages
        if body.get("jsonrpc") == "2.0":
            params = body.get("params", {})
            request_id = body.get("id")
            
            print(f"🔄 Processing MCP method: {method}")
            
            if method == "initialize":
                print("🚀 INITIALIZE: Setting up MCP connection")
                
                # Use 2024-11-05 as per Anthropic engineer's feedback
                client_version = params.get("protocolVersion", "2024-11-05")
                server_version = "2024-11-05"  # Fixed version per Anthropic engineer
                print(f"🔄 Client requested version: {client_version}")
                print(f"🔄 Returning fixed version: {server_version}")
                
                response_data = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": server_version,
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            },
                            "resources": {},
                            "prompts": {},
                            "logging": {}
                        },
                        "serverInfo": {
                            "name": "commerce-router",
                            "version": "1.0.0"
                        }
                    }
                }
                print(f"✅ INITIALIZE SUCCESS: {json.dumps(response_data, indent=2)}")
                return JSONResponse(response_data)
            
            elif method == "notifications/initialized":
                print("📢 NOTIFICATIONS/INITIALIZED: Client confirming connection")
                print("🔧 Returning HTTP 202 Accepted with empty body as per MCP spec")
                # Per MCP spec: notifications MUST return 202 Accepted with no body
                return JSONResponse(content="", status_code=202)
            
            elif method == "tools/list":
                print("🔧 TOOLS/LIST: Claude is requesting available tools!")
                response_data = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "route_commerce_message",
                                "description": "Route commerce messages to specialized services like Domino's Pizza, OpenTable restaurants, and Uber ride booking. Handles user sessions and connects to appropriate MCP services.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "user_id": {
                                            "type": "string",
                                            "description": "Unique user identifier for session management and profile lookup. If not provided, a temporary ID will be generated, but user profile features will be limited."
                                        },
                                        "message": {
                                            "type": "string", 
                                            "description": "User's commerce message (e.g., 'I want pizza', 'book a restaurant', 'I need an Uber')"
                                        },
                                        "force_service": {
                                            "type": "string",
                                            "description": "Optional: force specific service (dominos, opentable, uber)",
                                            "enum": ["dominos", "opentable", "uber"]
                                        },
                                        "force_new_session": {
                                            "type": "boolean",
                                            "description": "Optional: force starting a new session even if user has an active one. Use when user clearly switches context (e.g. from restaurant booking to ride booking)"
                                        }
                                    },
                                    "required": ["message"]
                                }
                            }
                        ]
                    }
                }
                print(f"✅ TOOLS/LIST SUCCESS: Returned 1 tool (route_commerce_message)")
                return JSONResponse(response_data)
            
            elif method == "tools/call":
                print("🎯 TOOLS/CALL: Claude is using a tool!")
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                print(f"   Tool: {tool_name}")
                print(f"   Arguments: {json.dumps(arguments, indent=2)}")
                
                if tool_name == "route_commerce_message":
                    try:
                        print("🔄 Executing route_commerce_message...")
                        
                        # Generate fallback user_id if not provided
                        user_id = arguments.get("user_id")
                        if not user_id:
                            import hashlib
                            message_hash = hashlib.md5(arguments.get("message", "").encode()).hexdigest()[:8]
                            user_id = f"claude-user-{message_hash}"
                            print(f"🔄 Generated fallback user_id: {user_id}")
                        
                        result = await route_commerce_message_with_profiles(
                            user_id=user_id,
                            message=arguments.get("message"),
                            force_service=arguments.get("force_service"),
                            force_new_session=arguments.get("force_new_session", False)
                        )
                        
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": result
                                    }
                                ]
                            }
                        }
                        print(f"✅ TOOLS/CALL SUCCESS: Tool executed successfully")
                        return JSONResponse(response_data)
                        
                    except Exception as e:
                        print(f"❌ TOOLS/CALL ERROR: {str(e)}")
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32000,
                                "message": f"Tool execution failed: {str(e)}"
                            }
                        })
                
                else:
                    print(f"❌ UNKNOWN TOOL: {tool_name}")
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    })
            
            else:
                print(f"❌ UNKNOWN METHOD: {method}")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                })
        
        else:
            print("❌ INVALID JSON-RPC: Missing jsonrpc field")
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request - not valid JSON-RPC 2.0"
                }
            })
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON PARSE ERROR: {str(e)}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": f"Parse error - Invalid JSON: {str(e)}"
            }
        })
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {str(e)}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        })

@fastapi_app.get("/mcp")
async def mcp_get_handler(request: Request):
    """Handle GET requests with detailed logging"""
    log_request_details(request)
    
    print("🚨 GET REQUEST DETECTED!")
    print("💡 This is likely a health check or monitoring request")
    print("💡 MCP protocol only uses POST requests")
    
    return JSONResponse({
        "status": "healthy",
        "protocol": "MCP over HTTP",
        "message": "This endpoint only accepts POST requests for MCP protocol",
        "note": "GET requests are for health checks only"
    })

@fastapi_app.get("/health")
async def health():
    return {"status": "healthy", "type": "MCP Server", "protocol": "HTTP", "version": "2024-11-05"}

@fastapi_app.get("/")
async def root():
    return {
        "name": "Commerce Router MCP Server",
        "description": "HTTP-based MCP server for routing commerce messages to specialized services",
        "mcp_endpoint": "/mcp",
        "protocol_version": "2024-11-05",
        "services": ["dominos", "opentable"]
    }

# Deploy as Modal ASGI app
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("router-mcp-secrets")],
)
@modal.asgi_app()
def commerce_router_mcp():
    return fastapi_app

if __name__ == "__main__":
    print("🚀 Deploy with: modal deploy mcp_server_http.py")
    print("📍 Your MCP URL will be: https://usman-hanif--commerce-router-mcp-http-commerce-router-mcp.modal.run/mcp")
    print("\n🔧 Add to Claude Desktop config:")
    config = {
        "mcpServers": {
            "commerce-router": {
                "url": "https://usman-hanif--commerce-router-mcp-http-commerce-router-mcp.modal.run/mcp",
                "transport": "http"
            }
        }
    }
    print(json.dumps(config, indent=2)) 