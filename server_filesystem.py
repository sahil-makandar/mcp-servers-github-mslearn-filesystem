"""MCP Server - File System Operations"""
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("filesystem")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="save_file",
            description="Save content to a file in data/<topic>_<datetime>/<filename>",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic/category for organizing files"},
                    "filename": {"type": "string", "description": "Filename with extension (e.g., code.py, notes.md)"},
                    "content": {"type": "string", "description": "File content to save"}
                },
                "required": ["topic", "filename", "content"]
            }
        ),
        Tool(
            name="read_file",
            description="Read content from a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to file relative to project root"}
                },
                "required": ["filepath"]
            }
        ),
        Tool(
            name="list_saved_files",
            description="List all saved files in data directory",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "save_file":
        topic = arguments["topic"].replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_path = Path(f"data/{topic}_{timestamp}")
        dir_path.mkdir(parents=True, exist_ok=True)
        
        file_path = dir_path / arguments["filename"]
        file_path.write_text(arguments["content"], encoding="utf-8")
        
        return [TextContent(type="text", text=f"File saved: {file_path}")]
    
    elif name == "read_file":
        file_path = Path(arguments["filepath"])
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            return [TextContent(type="text", text=content)]
        return [TextContent(type="text", text="File not found")]
    
    elif name == "list_saved_files":
        data_dir = Path("data")
        if not data_dir.exists():
            return [TextContent(type="text", text="No files saved yet")]
        
        files = []
        for item in data_dir.rglob("*"):
            if item.is_file():
                files.append(str(item))
        
        return [TextContent(type="text", text=json.dumps({"files": files}))]
    
    return [TextContent(type="text", text="Unknown tool")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
