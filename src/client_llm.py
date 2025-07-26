import asyncio
import sys
import os
import json
from contextlib import AsyncExitStack
from typing import Optional, List, Dict
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

# Load environment variables
load_dotenv("config/.env.")
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    print("❌ Error: GROQ_API_KEY not found in config/.env file")
    sys.exit(1)

# Groq/OpenAI client setup
groq_client = OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1"
)

class MCPClient:
    def __init__(self):
        self.openai_client = groq_client
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.available_tools = []
        self.conversation_history = []
        self.complete_logs = []

    async def connect_to_server(self, server_script_path: str):
        """Connect to the MCP server script (.py) via stdio."""
        if not os.path.exists(server_script_path):
            raise FileNotFoundError(f"Server script not found: {server_script_path}")
        
        if not server_script_path.endswith(".py"):
            raise ValueError("Expected a .py server script path")

        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path]
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            await self.session.initialize()

            tool_response = await self.session.list_tools()
            self.available_tools = tool_response.tools

            print(f"\n✅ Connected to MCP server successfully!")
            print(f"📚 Available tools: {', '.join([tool.name for tool in self.available_tools])}")
            
            # Auto-initialize index on first run
            await self._auto_initialize_if_needed()
            
        except Exception as e:
            print(f"❌ Failed to connect to server: {str(e)}")
            raise

    async def _auto_initialize_if_needed(self):
        """Check if file index exists and initialize if needed."""
        if os.path.exists("file_index.db"):
            print("📂 File index found. Ready for fast searches!")
        else:
            print("🔄 No file index found. Initializing for faster searches...")
            try:
                result = await self.session.call_tool("initialize_index", {
                    "directories": "desktop,downloads,documents"
                })
                if hasattr(result.content, 'text'):
                    content = json.loads(result.content.text)
                    if content.get("status") == "success":
                        print(f"✅ {content.get('message', 'Index initialized')}")
                    else:
                        print(f"⚠️ Index initialization warning: {content}")
            except Exception as e:
                print(f"⚠️ Could not auto-initialize index: {e}")

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt based on available tools."""
        tool_descriptions = {}
        for tool in self.available_tools:
            tool_descriptions[tool.name] = tool.description or "No description available"
        
        return f"""You are a helpful file system assistant with access to these tools:

SEARCH & DISCOVERY:
- search_files: Find files by name patterns. Use for "find", "search", "look for" requests
- find_latest_file: Find most recent file matching a pattern  
- list_directory: Show contents of folders

FILE OPERATIONS:
- read_file: Read text file contents. Only use when user asks to "read", "show", "display" content
- create_file: Create new files with optional templates
- write_file: Overwrite existing file content
- append_file: Add content to existing files
- delete_path: Delete files/folders (requires confirmation)
- move_file: Move, rename, or relocate files

METADATA & INFO:
- get_metadata: Get detailed file information
- initialize_index: Set up fast file indexing (run once)

IMPORTANT RULES:
1. Only call tools the user explicitly requests or that are necessary for their task
2. For deletions, always get confirmation first (delete_path with confirm=False, then confirm=True)
3. When multiple files match a search, show options and ask user to choose
4. Use search_files for finding files, not read_file
5. Be conversational and helpful in your responses
6. Handle errors gracefully and suggest alternatives

Current tools available: {', '.join(tool_descriptions.keys())}"""

    async def process_query(self, query: str) -> str:
        """Process a user query using LLM and available tools."""
        # Add user query to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        # Keep conversation history manageable (last 10 exchanges)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            *self.conversation_history
        ]

        # Prepare tools for OpenAI API
        available_tools = []
        for tool in self.available_tools:
            available_tools.append({
                "name": tool.name,
                "description": tool.description or "No description available.",
                "parameters": tool.inputSchema
            })

        response_parts = []
        max_turns = 8
        turn = 0

        try:
            while turn < max_turns:
                turn += 1
                
                # Call LLM
                api_response = self.openai_client.chat.completions.create(
                    model="llama3-8b-8192",  # Using larger model for better reasoning
                    messages=messages,
                    tools=[{"type": "function", "function": tool} for tool in available_tools],
                    tool_choice="auto",
                    temperature=0.1  # Lower temperature for more consistent responses
                )

                assistant_msg = api_response.choices[0].message
                
                # Handle tool calls
                if assistant_msg.tool_calls:
                    messages.append({
                        "role": "assistant", 
                        "content": assistant_msg.content,
                        "tool_calls": assistant_msg.tool_calls
                    })
                    
                    tool_results = []
                    
                    for tool_call in assistant_msg.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError as e:
                            error_msg = f"Invalid tool arguments for {tool_name}: {e}"
                            tool_results.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "content": error_msg
                            })
                            continue
                        
                        print(f"🔧 Executing: {tool_name}({tool_args})")
                        self.complete_logs.append(tool.name)
                        try:
                            # Execute tool
                            result = await self.session.call_tool(tool_name, tool_args)
                            
                            # Extract content
                            if hasattr(result.content, 'text'):
                                content = result.content.text
                            else:
                                content = str(result.content)
                            
                            tool_results.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "content": content
                            })
                            
                        except Exception as e:
                            error_msg = f"Error executing {tool_name}: {str(e)}"
                            print(f"❌ {error_msg}")
                            tool_results.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool", 
                                "content": error_msg
                            })
                    
                    # Add tool results to conversation
                    messages.extend(tool_results)
                
                # Handle text response
                elif assistant_msg.content:
                    response_parts.append(assistant_msg.content)
                    # Add to conversation history
                    self.conversation_history.append({
                        "role": "assistant", 
                        "content": assistant_msg.content
                    })
                    break
                
                else:
                    response_parts.append("⚠️ No response generated.")
                    break

            if turn >= max_turns:
                response_parts.append("⚠️ Maximum conversation turns reached.")

        except Exception as e:
            error_msg = f"❌ Error processing query: {str(e)}"
            print(error_msg)
            return error_msg

        final_response = "\n".join(response_parts) if response_parts else "❌ No response generated."
        return final_response

    def _handle_special_commands(self, query: str) -> Optional[str]:
        """Handle special client commands."""
        query_lower = query.lower().strip()
        
        if query_lower in ['help', '/help']:
            return self._show_help()
        elif query_lower in ['tools', '/tools']:
            return self._show_tools()
        elif query_lower in ['clear', '/clear']:
            self.conversation_history.clear()
            return "🧹 Conversation history cleared."
        elif query_lower.startswith('/model '):
            model_name = query[7:].strip()
            return self._change_model(model_name)
        
        return None

    def _show_help(self) -> str:
        """Show help information."""
        return """
🤖 MCP File System Assistant Help

NATURAL LANGUAGE EXAMPLES:
• "Find my resume in downloads"
• "Show me the latest file with 'project' in the name"
• "Read the contents of config.txt"
• "Create a new Python file called script.py"
• "Delete the old backup folder"
• "Move myfile.txt to the desktop"
• "List all files in my documents folder"

SPECIAL COMMANDS:
• help or /help - Show this help
• tools or /tools - List available tools
• clear or /clear - Clear conversation history
• /model <name> - Change AI model
• quit - Exit the application

TIPS:
• Be specific about file locations when possible
• The system will ask for confirmation before deleting files
• Use "latest" or "newest" to find recent files
• You can refer to folders like "desktop", "downloads", "documents"
"""

    def _show_tools(self) -> str:
        """Show available tools and their descriptions."""
        tool_info = ["🛠️ Available Tools:\n"]
        for tool in self.available_tools:
            description = tool.description or "No description available"
            tool_info.append(f"• {tool.name}: {description}")
        return "\n".join(tool_info)

    def _change_model(self, model_name: str) -> str:
        """Change the AI model (if supported)."""
        supported_models = [
            "llama3-70b-8192",
            "llama3-8b-8192", 
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
        
        if model_name in supported_models:
            # Update the client to use new model
            # Note: This would require recreating the OpenAI client
            return f"🔄 Model change requested to {model_name}. (Restart required to take effect)"
        else:
            return f"❌ Unsupported model. Available models: {', '.join(supported_models)}"

    async def chat_loop(self):
        """Interactive chat loop with enhanced features."""
        print("\n🚀 MCP File System Assistant Started!")
        print("Type 'help' for usage examples or 'quit' to exit.")
        print("="*60)
        
        while True:
            try:
                query = input("\n💬 You: ").strip()
                
                if not query:
                    continue
                    
                if query.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                
                # Handle special commands
                special_response = self._handle_special_commands(query)
                if special_response:
                    print(f"\n🤖 Assistant: {special_response}")
                    continue
                
                # Process normal queries
                print("\n🤖 Assistant: ", end="", flush=True)
                response = await self.process_query(query)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                print("Please try again or type 'quit' to exit.")

    async def batch_process(self, commands: List[str]) -> List[str]:
        """Process multiple commands in batch mode."""
        results = []
        for i, command in enumerate(commands):
            print(f"\n📝 Processing command {i+1}/{len(commands)}: {command}")
            try:
                result = await self.process_query(command)
                results.append(result)
                print(f"✅ Command {i+1} completed")
            except Exception as e:
                error_msg = f"❌ Command {i+1} failed: {str(e)}"
                results.append(error_msg)
                print(error_msg)
        return results

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.exit_stack.aclose()
            print("🧹 Cleanup completed.")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

def print_banner():
    """Print application banner."""
    banner = """
            MCP File System Assistant                                                           

            """
    print(banner)

async def main():
    """Main application entry point."""
    print_banner()
    
    if len(sys.argv) < 2:
        print("❌ Usage: python client.py <path_to_server_script> [--batch <commands_file>]")
        print("\nExamples:")
        print("  python client.py server.py")
        print("  python client.py server.py --batch commands.txt")
        sys.exit(1)

    server_script = sys.argv[1]
    batch_mode = "--batch" in sys.argv
    
    client = MCPClient()
    
    try:
        # Connect to server
        print("🔄 Connecting to MCP server...")
        await client.connect_to_server(server_script)
        
        if batch_mode:
            # Batch processing mode
            if len(sys.argv) < 4:
                print("❌ Batch mode requires a commands file")
                sys.exit(1)
            
            commands_file = sys.argv[3]
            if not os.path.exists(commands_file):
                print(f"❌ Commands file not found: {commands_file}")
                sys.exit(1)
            
            print(f"📜 Running in batch mode with commands from: {commands_file}")
            
            try:
                with open(commands_file, 'r', encoding='utf-8') as f:
                    commands = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                results = await client.batch_process(commands)
                
                # Save results
                output_file = f"batch_results_{int(asyncio.get_event_loop().time())}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for i, (cmd, result) in enumerate(zip(commands, results)):
                        f.write(f"Command {i+1}: {cmd}\n")
                        f.write(f"Result: {result}\n")
                        f.write("-" * 60 + "\n")
                
                print(f"📄 Batch results saved to: {output_file}")
                
            except Exception as e:
                print(f"❌ Batch processing failed: {e}")
        
        else:
            # Interactive mode
            await client.chat_loop()
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)