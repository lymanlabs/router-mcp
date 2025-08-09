"""
OpenTable MCP Server on Modal Labs
Converts stdio-based MCP to HTTP-accessible endpoint
"""

import modal
import os
from pathlib import Path

# Create Modal app
app = modal.App("opentable-mcp-server")

# Define the image with required dependencies
image = modal.Image.debian_slim(python_version="3.11").pip_install([
    "mcp>=1.2.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "httpx>=0.25.0",
    "python-dotenv>=1.0.0",
    # Add any OpenTable-specific dependencies here
    "opentable-mcp-server"  # If it's a pip package
])

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("opentable-secrets")  # You'll create this in Modal
    ],
    allow_concurrent_inputs=100,
    timeout=300,
)
@modal.web_endpoint(
    method="POST",
    label="opentable-mcp",
)
def opentable_mcp_endpoint(request):
    """
    HTTP endpoint that wraps the OpenTable MCP
    """
    import json
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    # Get the OpenTable org key from environment
    OPENTABLE_ORG_KEY = os.getenv("OPENTABLE_ORG_KEY")
    
    if not OPENTABLE_ORG_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "OPENTABLE_ORG_KEY not configured"}
        )
    
    try:
        # Parse the MCP request
        body = request.json()
        
        # Here you'd integrate with your actual OpenTable MCP code
        # This is where you'd call the OpenTable MCP functions
        # and return MCP-formatted responses
        
        # Example response structure (you'll replace this with actual MCP logic)
        if body.get("method") == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "search_restaurants",
                            "description": "Search for restaurants by location",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "location": {"type": "string"},
                                    "cuisine": {"type": "string"},
                                    "party_size": {"type": "integer"}
                                },
                                "required": ["location"]
                            }
                        },
                        {
                            "name": "book_reservation",
                            "description": "Book a restaurant reservation",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "restaurant_id": {"type": "string"},
                                    "date_time": {"type": "string"},
                                    "party_size": {"type": "integer"}  
                                },
                                "required": ["restaurant_id", "date_time", "party_size"]
                            }
                        }
                    ]
                }
            })
        
        elif body.get("method") == "tools/call":
            tool_name = body.get("params", {}).get("name")
            arguments = body.get("params", {}).get("arguments", {})
            
            if tool_name == "search_restaurants":
                # Call your OpenTable search logic here
                result = f"Searching restaurants in {arguments.get('location')}..."
                
            elif tool_name == "book_reservation":
                # Call your OpenTable booking logic here  
                result = f"Booking reservation at {arguments.get('restaurant_id')}..."
                
            else:
                result = f"Unknown tool: {tool_name}"
            
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            })
        
        else:
            return JSONResponse({
                "jsonrpc": "2.0", 
                "id": body.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {body.get('method')}"
                }
            })
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id", 0),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
        )

# Health check endpoint
@app.function(image=image)
@modal.web_endpoint(method="GET", label="health")
def health_check():
    return {"status": "healthy", "service": "opentable-mcp"}

# Deploy script
if __name__ == "__main__":
    print("🚀 Deploying OpenTable MCP to Modal Labs...")
    print("After deployment, your MCP will be available at:")
    print("https://your-username--opentable-mcp-server-opentable-mcp.modal.run") 