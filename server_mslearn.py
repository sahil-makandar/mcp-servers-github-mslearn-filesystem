"""MCP Server - Microsoft Learn"""
import asyncio
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("mslearn")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_mslearn",
            description="Search Microsoft Learn documentation and tutorials",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (e.g., 'Azure Functions', 'C# async')"},
                    "limit": {"type": "number", "description": "Number of results (default 5)", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_azure_services",
            description="Get information about Azure services",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Service category (e.g., 'compute', 'ai', 'database')"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    async with httpx.AsyncClient() as client:
        if name == "search_mslearn":
            # Using Microsoft Learn API
            limit = arguments.get("limit", 5)
            query = arguments["query"]
            
            # Microsoft Learn search endpoint
            response = await client.get(
                f"https://learn.microsoft.com/api/search?search={query}&locale=en-us&$top={limit}"
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get("results", [])[:limit]:
                    results.append({
                        "title": item.get("title", "No title"),
                        "description": item.get("description", "No description"),
                        "url": f"https://learn.microsoft.com{item.get('url', '')}",
                        "type": item.get("type", "article")
                    })
                
                return [TextContent(type="text", text=json.dumps({"results": results}, indent=2))]
            else:
                # Fallback with simulated data
                results = [{
                    "title": f"Microsoft Learn: {query}",
                    "description": f"Documentation and tutorials about {query}",
                    "url": f"https://learn.microsoft.com/search/?terms={query}",
                    "type": "documentation"
                }]
                return [TextContent(type="text", text=json.dumps({"results": results}, indent=2))]
        
        elif name == "get_azure_services":
            category = arguments.get("category", "all")
            
            # Simulated Azure services data
            services = {
                "compute": ["Azure Virtual Machines", "Azure Functions", "Azure App Service", "Azure Kubernetes Service"],
                "ai": ["Azure OpenAI", "Azure Cognitive Services", "Azure Machine Learning", "Azure AI Search"],
                "database": ["Azure SQL Database", "Azure Cosmos DB", "Azure Database for PostgreSQL"],
                "storage": ["Azure Blob Storage", "Azure Files", "Azure Data Lake Storage"]
            }
            
            if category in services:
                result = {"category": category, "services": services[category]}
            else:
                result = {"categories": list(services.keys()), "all_services": services}
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    return [TextContent(type="text", text="Unknown tool")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
