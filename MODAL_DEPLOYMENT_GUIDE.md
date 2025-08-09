# 🚀 Deploy OpenTable MCP to Modal Labs

## Step 1: Install Modal CLI

```bash
pip install modal
```

## Step 2: Setup Modal Account

```bash
# Login to Modal (will open browser)
modal setup

# Create a new token if needed
modal token new
```

## Step 3: Create Secrets in Modal

```bash
# Create secret with your OpenTable org key
modal secret create opentable-secrets OPENTABLE_ORG_KEY=a7a7a7a7-a7a7-a7a7-a7a7-a7a7a7a7a7a7
```

## Step 4: Integrate Your Actual OpenTable MCP Code

Replace the example code in `modal_opentable_mcp.py` with your actual OpenTable MCP logic:

```python
# Instead of:
# result = f"Searching restaurants in {arguments.get('location')}..."

# Use your actual OpenTable MCP functions:
from your_opentable_mcp import search_restaurants, book_reservation

if tool_name == "search_restaurants":
    result = search_restaurants(
        location=arguments.get('location'),
        cuisine=arguments.get('cuisine'),
        party_size=arguments.get('party_size', 2)
    )
```

## Step 5: Deploy to Modal

```bash
# Deploy the MCP server
modal deploy modal_opentable_mcp.py

# You'll get a URL like:
# https://your-username--opentable-mcp-server-opentable-mcp.modal.run
```

## Step 6: Test the Deployment

```bash
# Test health endpoint
curl https://your-username--opentable-mcp-server-health.modal.run

# Test MCP tools/list
curl -X POST https://your-username--opentable-mcp-server-opentable-mcp.modal.run \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Step 7: Add to Router MCP

Once deployed, add the URL to your Router MCP:

```python
SERVICE_CONFIGS = {
    "dominos": { ... },
    "opentable": {
        "keywords": ["restaurant", "reservation", "book table", "dinner"],
        "mcp_config": {
            "type": "url",
            "url": "https://your-username--opentable-mcp-server-opentable-mcp.modal.run",
            "name": "opentable-mcp"
        },
        "description": "OpenTable restaurant reservation service",
        "system_prompt": "You are a helpful OpenTable assistant..."
    }
}
```

## Tips:

1. **Find your actual MCP code**: Look for the OpenTable MCP source code
2. **Extract the tools**: Identify what tools/functions it provides
3. **Wrap HTTP around it**: Use the Modal template to wrap it with HTTP
4. **Test thoroughly**: Make sure it responds to MCP protocol requests
5. **Update Router**: Add the Modal URL to your Router MCP

## Cost:

Modal Labs free tier should handle development/testing. Production usage has reasonable pricing. 