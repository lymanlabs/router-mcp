"""
HTTP-based MCP Server for Commerce Router
"""

import modal
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import json

app = modal.App("commerce-router-mcp")

# Image with dependencies and local code
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
    .add_local_file("requirements.txt", remote_path="/app/requirements.txt")
)

# Create FastAPI app for MCP
fastapi_app = FastAPI()

@fastapi_app.post("/mcp")
async def mcp_handler(request: Request):
    """HTTP MCP endpoint"""
    try:
        import sys
        sys.path.append("/app")
        
        # Import router function
        from router_profiles_enhanced import route_commerce_message_with_profiles
        
        # Parse MCP request
        body = await request.json()
        
        # Handle MCP protocol messages
        if body.get("jsonrpc") == "2.0":
            method = body.get("method")
            params = body.get("params", {})
            request_id = body.get("id")
            
            # Handle MCP initialize
            if method == "initialize":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "commerce-router",
                            "version": "1.0.0"
                        }
                    }
                })
            
            # Handle tools/list
            elif method == "tools/list":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "route_commerce_message",
                                "description": "Route commerce messages to specialized services (Domino's, OpenTable, etc.)",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "user_id": {
                                            "type": "string",
                                            "description": "Unique user identifier"
                                        },
                                        "message": {
                                            "type": "string", 
                                            "description": "User's commerce message"
                                        },
                                        "force_service": {
                                            "type": "string",
                                            "description": "Optional: force specific service (dominos, opentable)"
                                        }
                                    },
                                    "required": ["user_id", "message"]
                                }
                            }
                        ]
                    }
                })
            
            # Handle tools/call
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "route_commerce_message":
                    try:
                        result = await route_commerce_message_with_profiles(
                            user_id=arguments.get("user_id"),
                            message=arguments.get("message"),
                            force_service=arguments.get("force_service")
                        )
                        
                        return JSONResponse({
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
                        })
                        
                    except Exception as e:
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32000,
                                "message": f"Tool execution failed: {str(e)}"
                            }
                        })
                
                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    })
            
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown method: {method}"
                    }
                })
        
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                }
            })
            
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        })

@fastapi_app.get("/health")
async def health():
    return {"status": "healthy", "type": "MCP Server"}

# Deploy as Modal web app
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("router-mcp-secrets")],
)
@modal.asgi_app()
def commerce_router_mcp():
    return fastapi_app

if __name__ == "__main__":
    print("🚀 Deploy with: modal deploy deploy_modal.py")
    print("📍 Your MCP URL will be: https://your-username--commerce-router-mcp.modal.run/mcp")
    print("🔧 Add to Claude Desktop config:")
    print(json.dumps({
        "mcpServers": {
            "commerce-router": {
                "url": "https://your-username--commerce-router-mcp.modal.run/mcp",
                "transport": "http"
            }
        }
    }, indent=2)) 