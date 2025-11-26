"""Multi-Server MCP Client - GitHub + MS Learn + FileSystem"""
import asyncio
import json
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class MultiServerClient:
    def __init__(self):
        self.sessions = {}
        self.ai = None
        self.all_tools = []
        self.exit_stack = AsyncExitStack()
        self.conversation_history = []
        
    async def connect(self):
        servers = {
            "github": StdioServerParameters(command="python", args=["server_github.py"]),
            "mslearn": StdioServerParameters(command="python", args=["server_mslearn.py"]),
            "filesystem": StdioServerParameters(command="python", args=["server_filesystem.py"])
        }
        
        print("Connecting to MCP servers...")
        
        for name, params in servers.items():
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(params))
            stdio, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
            await session.initialize()
            
            response = await session.list_tools()
            self.sessions[name] = {"session": session, "tools": response.tools}
            
            for tool in response.tools:
                self.all_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": f"[{name.upper()}] {tool.description}",
                        "parameters": tool.inputSchema
                    }
                })
            
            print(f"  ✓ {name}: {len(response.tools)} tools")
        
        self.ai = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2025-01-01-preview"
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        
        print(f"\n✓ All servers connected ({len(self.all_tools)} total tools)")
        print("✓ Azure OpenAI ready\n")
    
    async def find_tool_server(self, tool_name: str):
        for server_name, data in self.sessions.items():
            for tool in data["tools"]:
                if tool.name == tool_name:
                    return data["session"]
        return None
    
    async def chat(self, user_msg: str):
        system_prompt = """You are a technical assistant that ALWAYS uses tools to fetch real data.

AVAILABLE TOOLS:
- search_github_repos: Search GitHub for code, libraries, examples
- get_repo_info: Get detailed repository information
- get_trending_repos: Find trending repositories
- search_mslearn: Search Microsoft Learn for documentation, tutorials
- get_azure_services: Get Azure services information
- save_file: Save content to files (data/<topic>_<datetime>/<filename>)
- read_file: Read saved files
- list_saved_files: List all saved files

CRITICAL RULES:
1. For ANY technical question, programming topic, or technology query:
   - ALWAYS search BOTH search_mslearn AND search_github_repos
   - Use MS Learn for documentation/tutorials
   - Use GitHub for code examples and implementations

2. When user asks for code examples or more details:
   - Use search_github_repos to find actual code
   - Use get_repo_info to get specific repository details
   - Provide real code from GitHub, not made-up examples

3. When user says "save it", "save this", "save to file":
   - Use save_file with content from previous conversation

4. NEVER provide generic answers - ALWAYS use tools to get real, current data

Default behavior: Search MS Learn + GitHub for every technical question."""
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_msg})
        
        # Build messages with history
        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
        
        print(f"\n[Thinking...]")
        
        response = await self.ai.chat.completions.create(
            model=self.deployment,
            messages=messages,
            tools=self.all_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            results = []
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"\n[Calling {tool_name}]")
                print(f"  Args: {tool_args}")
                
                session = await self.find_tool_server(tool_name)
                if session:
                    result = await session.call_tool(tool_name, tool_args)
                    result_text = result.content[0].text
                    results.append(result_text)
                    print(f"  ✓ Done")
            
            # Get final response from AI with tool results
            messages.append({"role": "assistant", "content": message.content, "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in message.tool_calls
            ]})
            
            for i, tool_call in enumerate(message.tool_calls):
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": results[i]
                })
            
            final_response = await self.ai.chat.completions.create(
                model=self.deployment,
                messages=messages
            )
            
            assistant_msg = final_response.choices[0].message.content
            print(f"\n{assistant_msg}\n")
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": assistant_msg})
        else:
            assistant_msg = message.content
            print(f"\n{assistant_msg}\n")
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": assistant_msg})
    
    async def run(self):
        print("="*60)
        print("MULTI-SERVER MCP CLIENT")
        print("="*60)
        print("Connected to: GitHub | Microsoft Learn | FileSystem")
        print("="*60)
        print("\nExamples:")
        print("  - Search GitHub for Python ML libraries")
        print("  - What are Azure AI services?")
        print("  - Find trending JavaScript repos and save to file")
        print("  - Search MS Learn for Azure Functions tutorials")
        print("\nType 'exit' to quit\n")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(None, input, "You: ")
                user_input = user_input.strip()
                if not user_input: continue
                if user_input.lower() == 'exit': break
                
                await self.chat(user_input)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}\n")
    
    async def cleanup(self):
        await self.exit_stack.aclose()

async def main():
    client = MultiServerClient()
    try:
        await client.connect()
        await client.run()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
