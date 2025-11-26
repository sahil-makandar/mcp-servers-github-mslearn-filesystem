"""MCP Server - GitHub API"""
import asyncio
import json
import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent

app = Server("github")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_github_repos",
            description="Search GitHub repositories by query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (e.g., 'machine learning python')"},
                    "limit": {"type": "number", "description": "Number of results (default 5)", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_repo_info",
            description="Get detailed information about a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"}
                },
                "required": ["owner", "repo"]
            }
        ),
        Tool(
            name="get_trending_repos",
            description="Get trending repositories (simulated - top starred repos)",
            inputSchema={
                "type": "object",
                "properties": {
                    "language": {"type": "string", "description": "Programming language filter (optional)"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Authorization": f"token {token}"} if token else {}
    
    async with httpx.AsyncClient() as client:
        if name == "search_github_repos":
            limit = arguments.get("limit", 5)
            response = await client.get(
                f"https://api.github.com/search/repositories?q={arguments['query']}&sort=stars&per_page={limit}",
                headers=headers
            )
            data = response.json()
            
            results = []
            for repo in data.get("items", [])[:limit]:
                results.append({
                    "name": repo["full_name"],
                    "description": repo.get("description", "No description"),
                    "stars": repo["stargazers_count"],
                    "url": repo["html_url"],
                    "language": repo.get("language", "Unknown")
                })
            
            return [TextContent(type="text", text=json.dumps({"repositories": results}, indent=2))]
        
        elif name == "get_repo_info":
            response = await client.get(
                f"https://api.github.com/repos/{arguments['owner']}/{arguments['repo']}",
                headers=headers
            )
            repo = response.json()
            
            info = {
                "name": repo["full_name"],
                "description": repo.get("description", "No description"),
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "language": repo.get("language", "Unknown"),
                "url": repo["html_url"],
                "topics": repo.get("topics", []),
                "created": repo["created_at"],
                "updated": repo["updated_at"]
            }
            
            return [TextContent(type="text", text=json.dumps(info, indent=2))]
        
        elif name == "get_trending_repos":
            query = "stars:>10000"
            if "language" in arguments and arguments["language"]:
                query += f" language:{arguments['language']}"
            
            response = await client.get(
                f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=10",
                headers=headers
            )
            data = response.json()
            
            results = []
            for repo in data.get("items", [])[:10]:
                results.append({
                    "name": repo["full_name"],
                    "description": repo.get("description", "No description"),
                    "stars": repo["stargazers_count"],
                    "language": repo.get("language", "Unknown")
                })
            
            return [TextContent(type="text", text=json.dumps({"trending": results}, indent=2))]
    
    return [TextContent(type="text", text="Unknown tool")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
