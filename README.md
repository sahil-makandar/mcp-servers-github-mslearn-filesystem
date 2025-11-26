# Multi-Server MCP Implementation (Github MCP, MS Learn MCP, FileSystem MCP, Azure OpenAI)

MCP servers for GitHub, Microsoft Learn, and filesystem with Azure OpenAI - Multi-server Model Context Protocol implementation

A **production-ready** MCP client that connects to multiple MCP servers simultaneously:
- 🐙 **GitHub Server**: Search repos, get repo info, trending repos
- 📚 **Microsoft Learn Server**: Search documentation, Azure services info
- 💾 **FileSystem Server**: Save/read files with automatic organization

## Architecture

```
                    ┌─────────────────┐
                    │   Azure OpenAI  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  MCP Client     │
                    │  (client.py)    │
                    └─┬─────┬────┬────┘
                      │     │    │
        ┌─────────────┘     │    └─────────────┐
        │                   │                  │
┌───────▼────────┐  ┌───────▼────────┐  ┌─────▼──────────┐
│ GitHub Server  │  │ MSLearn Server │  │ FileSystem     │
│ (stdio)        │  │ (stdio)        │  │ Server (stdio) │
└────────────────┘  └────────────────┘  └────────────────┘
```

## Features

### 1. GitHub Integration
- **search_github_repos**: Search repositories by query
- **get_repo_info**: Get detailed repo information
- **get_trending_repos**: Find trending repositories by language

### 2. Microsoft Learn Integration
- **search_mslearn**: Search MS Learn documentation
- **get_azure_services**: Get Azure services by category

### 3. File System Integration
- **save_file**: Auto-organized saving to `data/<topic>_<datetime>/<filename>`
- **read_file**: Read any file from project
- **list_saved_files**: List all saved files

## Setup

1. **Install dependencies** (if not already):
   ```bash
   pip install mcp openai python-dotenv httpx
   ```

2. **Configure `.env`** (in project root):
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
   AZURE_OPENAI_KEY=your-key
   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
   GITHUB_TOKEN=your-github-token  # Optional, for higher rate limits
   ```

3. **Run the client**:
   ```bash
   python client.py
   ```

## Usage Examples

### Example 1: Search GitHub and Save
```
You: Search GitHub for Python machine learning libraries and save the top 3 to a file

[AI will]:
1. Call search_github_repos with query "Python machine learning"
2. Format the results
3. Call save_file to save in data/github_search_20240115_143022/ml_libraries.md
```

### Example 2: Microsoft Learn Search
```
You: What are Azure AI services?

[AI will]:
1. Call get_azure_services with category "ai"
2. Present the list of Azure AI services
```

### Example 3: Combined Workflow
```
You: Find trending JavaScript repos, then search MS Learn for Node.js tutorials, and save everything to a file

[AI will]:
1. Call get_trending_repos with language "JavaScript"
2. Call search_mslearn with query "Node.js tutorials"
3. Combine results and call save_file to save in organized folder
```

### Example 4: Code Saving
```
You: Show me a Python async example and save it as async_example.py

[AI will]:
1. Generate Python async code
2. Call save_file with filename "async_example.py"
3. File saved to data/python_async_20240115_143530/async_example.py
```

## How It Works

### 1. Client Startup
- Spawns 3 MCP servers as subprocesses
- Each server communicates via stdio (JSON-RPC 2.0)
- Client establishes MCP sessions with all servers
- Collects all tools from all servers (9 total tools)

### 2. User Query Processing
- User types natural language query
- Client sends to Azure OpenAI with all 9 tools available
- OpenAI decides which tool(s) to call and with what arguments

### 3. Tool Execution
- Client identifies which server owns the requested tool
- Calls tool via MCP protocol (JSON-RPC over stdio)
- Server executes and returns result
- Client sends results back to OpenAI for final response

### 4. File Organization
When saving files, the filesystem server automatically creates:
```
data/
  ├── github_search_20240115_143022/
  │   ├── ml_libraries.md
  │   └── results.json
  ├── azure_services_20240115_144530/
  │   └── ai_services.txt
  └── python_code_20240115_145012/
      └── async_example.py
```

## MCP Protocol Compliance

✅ **Proper stdio transport** (JSON-RPC 2.0)  
✅ **Multiple server connections** (3 simultaneous sessions)  
✅ **Tool discovery** (list_tools from each server)  
✅ **Tool execution** (call_tool via proper protocol)  
✅ **OpenAI function calling** (native tools parameter)  
✅ **Automatic tool routing** (client finds correct server for each tool)


## Extending

### Add a New Server
1. Create `server_newservice.py` with MCP Server
2. Add to `servers` dict in `client.py`
3. Client automatically discovers and uses new tools

### Add New Tools
Just add to any server's `list_tools()` - client picks them up automatically!

## Notes

- **GitHub Token**: Optional but recommended for higher API rate limits
- **File Paths**: All relative to project root where client runs
- **Error Handling**: Graceful fallbacks for API failures
- **Concurrent Tools**: AI can call multiple tools in sequence

This is a **real-world MCP implementation** showing the power of multi-server orchestration!
