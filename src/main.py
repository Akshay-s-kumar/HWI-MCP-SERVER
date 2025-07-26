import asyncio
import json
import re
import os
import stat
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
import sys

# Load environment variables from config/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

config_path = os.path.join(os.path.dirname(sys.executable), 'config', '.env')
if not os.path.exists(config_path):
    config_path = os.path.join(os.path.abspath("."), 'config', '.env')
load_dotenv(config_path)

class FileChatbot:
    """
    A chatbot for interacting with the local file system, capable of
    searching, reading, creating, editing, and deleting files.
    
    NOTE: We added self.pending_intent to handle state for web requests.
    """
    def __init__(self, groq_api_key: str):
        if not groq_api_key:
            raise ValueError("Groq API key is missing. Please check your config/.env file.")
        self.groq_client = Groq(api_key=groq_api_key)
        self.pending_intent = None # State for confirmations

    def parse_user_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Parse user message to extract intent and parameters using the Groq API.
        This now includes intents for creating, editing, and deleting files.
        """
        system_prompt = """
        You are an intent parser for a file system chatbot. Analyze the user's message and extract the action and parameters.
        Actions can be: search_file, get_file_metadata, read_file, create_file, edit_file, delete_file, list_directory.
        
        - For "edit_file", also extract the "content" to write and determine if the mode is "append" or "overwrite".
        - For "create_file", extract the "content".
        - For "delete_file", extract the file path for deletion.

        Respond in JSON format.

        Examples:
        - "find my_report.docx" -> {"action": "search_file", "filename": "my_report.docx", "path": null}
        - "get metadata for C:/Users/Me/file.txt" -> {"action": "get_file_metadata", "path": "C:/Users/Me/file.txt"}
        - "read C:/data/info.txt" -> {"action": "read_file", "path": "C:/data/info.txt"}
        - "create a new file called hello.txt in my documents folder with the content 'Hello World'" -> {"action": "create_file", "path": "documents/hello.txt", "content": "Hello World"}
        - "append 'new line' to C:/files/log.txt" -> {"action": "edit_file", "path": "C:/files/log.txt", "content": "new line", "mode": "append"}
        - "delete the file temp.tmp from my desktop" -> {"action": "delete_file", "path": "desktop/temp.tmp"}
        """
        try:
            response = self.groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Error parsing intent: {e}")
            return {"action": "unknown", "original_message": user_message}

    def _get_file_permissions(self, mode: int) -> str:
        """Helper to convert stat mode to human-readable permission string."""
        permissions = []
        # User permissions
        permissions.append("r" if mode & stat.S_IRUSR else "-")
        permissions.append("w" if mode & stat.S_IWUSR else "-")
        permissions.append("x" if mode & stat.S_IXUSR else "-")
        # Group permissions
        permissions.append("r" if mode & stat.S_IRGRP else "-")
        permissions.append("w" if mode & stat.S_IWGRP else "-")
        permissions.append("x" if mode & stat.S_IXGRP else "-")
        # Other permissions
        permissions.append("r" if mode & stat.S_IROTH else "-")
        permissions.append("w" if mode & stat.S_IWOTH else "-")
        permissions.append("x" if mode & stat.S_IXOTH else "-")
        return "".join(permissions)

    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Retrieve detailed metadata for a specific file.
        Fulfills Requirement #2.
        """
        try:
            path = Path(self.resolve_path(file_path))
            if not path.exists():
                return {"success": False, "error": "File not found"}

            stat_info = path.stat()
            file_type, _ = mimetypes.guess_type(path)

            metadata = {
                "full_path": str(path.resolve()),
                "file_size_bytes": stat_info.st_size,
                "date_created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "date_modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "file_type": file_type or "unknown",
                "permissions": self._get_file_permissions(stat_info.st_mode),
            }
            return {"success": True, "metadata": metadata}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, filename: str, search_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for files by name, returning their absolute paths and basic metadata.
        Fulfills Requirement #1.
        """
        try:
            results = []
            # If no specific path provided, search in common locations
            if not search_path:
                search_paths = [Path.home() / "Desktop", Path.home() / "Documents", Path.home() / "Downloads", Path.home()]
            else:
                search_paths = [Path(self.resolve_path(search_path))]

            for s_path in search_paths:
                if s_path.exists() and s_path.is_dir():
                    for root, _, files in os.walk(s_path):
                        for file in files:
                            if filename.lower() in file.lower():
                                try:
                                    file_path = Path(root) / file
                                    results.append({
                                        "name": file,
                                        "path": str(file_path.resolve()),
                                        "size_bytes": file_path.stat().st_size,
                                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                                    })
                                except (OSError, IOError):
                                    continue # Ignore files that can't be accessed
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}

    def read_file_content(self, file_path: str, max_size: int = 1024 * 1024) -> Dict[str, Any]:
        """
        Read and return the content of a file.
        Part of Requirement #3.
        """
        try:
            path = Path(self.resolve_path(file_path))
            if not path.exists():
                return {"success": False, "error": "File not found"}
            if path.stat().st_size > max_size:
                return {"success": False, "error": f"File too large. Max size is {max_size} bytes."}
            
            content = path.read_text(encoding='utf-8', errors='ignore')
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_file(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """
        Create a new file with optional content.
        Part of Requirement #3.
        """
        try:
            path = Path(self.resolve_path(file_path))
            if path.exists():
                return {"success": False, "error": "File already exists at this path."}
            
            path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
            path.write_text(content, encoding='utf-8')
            return {"success": True, "message": f"File created at {path.resolve()}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def edit_file(self, file_path: str, content: str, mode: str = "append") -> Dict[str, Any]:
        """
        Edit a file by appending or overwriting content.
        Part of Requirement #3.
        """
        try:
            path = Path(self.resolve_path(file_path))
            if not path.exists():
                return {"success": False, "error": "File not found to edit."}

            write_mode = 'a' if mode == 'append' else 'w'
            with open(path, write_mode, encoding='utf-8') as f:
                if write_mode == 'a' and path.stat().st_size > 0:
                    f.write('\n') # Add a newline before appending
                f.write(content)
            
            return {"success": True, "message": f"File content {mode}ed successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete a file or an empty folder.
        Part of Requirement #3.
        """
        try:
            path = Path(self.resolve_path(file_path))
            if not path.exists():
                return {"success": False, "error": "File or folder not found."}

            if path.is_dir():
                if any(path.iterdir()):
                    return {"success": False, "error": "Directory is not empty. Cannot delete."}
                path.rmdir()
                message = f"Directory '{path.resolve()}' deleted successfully."
            else:
                path.unlink()
                message = f"File '{path.resolve()}' deleted successfully."
            
            return {"success": True, "message": message}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def resolve_path(self, path_hint: str) -> str:
        """Resolve common path hints like 'desktop' to their absolute paths."""
        if not path_hint:
            return str(Path.home())
        
        # Handle absolute paths first
        if Path(path_hint).is_absolute():
            return path_hint

        path_hint_lower = path_hint.lower()
        home = Path.home()
        
        # Simple mapping for keywords
        path_mapping = {
            "desktop": home / "Desktop",
            "documents": home / "Documents",
            "downloads": home / "Downloads",
            "home": home,
            "~": home,
        }
        
        # Check if the hint starts with a known keyword
        for keyword, base_path in path_mapping.items():
            if path_hint_lower.startswith(keyword):
                # Replace the keyword with the actual path
                # e.g., "desktop/myfile.txt" -> "C:/Users/User/Desktop/myfile.txt"
                rest_of_path = path_hint[len(keyword):].lstrip('/\\')
                return str(base_path / rest_of_path)

        # If no keyword matches, assume it's a relative path from the home directory
        return str(home / path_hint)

    async def execute_file_operation(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the appropriate file operation based on the parsed intent."""
        action = intent.get("action")
        path = intent.get("path")
        filename = intent.get("filename")
        content = intent.get("content")
        mode = intent.get("mode")

        try:
            if action == "search_file":
                return self.search_files(filename, path)
            elif action == "get_file_metadata":
                return self.get_file_metadata(path)
            elif action == "read_file":
                return self.read_file_content(path)
            elif action == "create_file":
                return self.create_file(path, content)
            elif action == "edit_file":
                return self.edit_file(path, content, mode)
            elif action == "delete_file":
                return self.delete_file(path)
            else:
                return {"success": False, "error": "I'm not sure how to handle that request."}
        except Exception as e:
            return {"success": False, "error": f"An error occurred during execution: {e}"}

    def format_response(self, operation_result: Dict[str, Any]) -> str:
        """Format the operation result into a natural language response."""
        system_prompt = "You are a helpful file system assistant. Format the JSON operation result into a concise, natural, and conversational response for the user. If there's an error, explain it clearly."
        
        # To save tokens, we can pre-format some common results
        if operation_result.get("success"):
            if "results" in operation_result:
                if not operation_result["results"]:
                    return "I couldn't find any files matching your search."
                # Don't send a huge list to the LLM
                summary = f"Found {len(operation_result['results'])} file(s). Here are the top 5:\n"
                for res in operation_result["results"][:5]:
                    summary += f"- `{res['name']}` at `{res['path']}`\n"
                return summary
            if "metadata" in operation_result:
                # Format metadata nicely
                meta = operation_result['metadata']
                return (
                    f"Here is the metadata for the file:\n"
                    f"- **Full Path**: `{meta['full_path']}`\n"
                    f"- **Size**: {meta['file_size_bytes']} bytes\n"
                    f"- **Created**: {meta['date_created']}\n"
                    f"- **Modified**: {meta['date_modified']}\n"
                    f"- **Type**: {meta['file_type']}\n"
                    f"- **Permissions**: {meta['permissions']}"
                )

        # For other cases, use the LLM
        context = f"Operation result: {json.dumps(operation_result, indent=2)}\nPlease format this into a natural response."
        try:
            response = self.groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            # Use markdown for better formatting
            return response.choices[0].message.content.replace('\n', '<br>')
        except Exception as e:
            return f"I encountered an error while formatting the response: {e}"

    async def handle_message(self, user_message: str) -> str:
        """
        Main web chat handler. Manages state for confirmations.
        """
        # Handle confirmation for deletion
        if self.pending_intent and self.pending_intent.get("action") == "delete_file":
            if user_message.lower() == 'yes':
                operation_result = await self.execute_file_operation(self.pending_intent)
                response = self.format_response(operation_result)
            else:
                response = "Deletion cancelled."
            self.pending_intent = None # Clear the pending state
            return response

        # Normal message flow
        intent = self.parse_user_intent(user_message)
        
        if intent.get("action") == "delete_file":
            # Store intent and ask for confirmation
            self.pending_intent = intent
            path_to_delete = self.resolve_path(intent.get("path", ""))
            return f"Are you sure you want to delete `{path_to_delete}`? Please type **yes** to confirm or anything else to cancel."

        operation_result = await self.execute_file_operation(intent)
        return self.format_response(operation_result)


# This part is for running the script directly from the command line.
# The Flask app will NOT use this.
async def main_cli():
    """Main function to run the chatbot in CLI mode."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("---")
        print("ERROR: GROQ_API_KEY environment variable not found.")
        print("Please create a 'config' folder with a '.env' file inside it.")
        print("Add the following line to the '.env' file:")
        print("GROQ_API_KEY='your-groq-api-key-here'")
        print("---")
        return

    print("Initializing File System Chatbot...")
    chatbot = FileChatbot(api_key)
    
    print("\nFile System Chatbot is ready! 🤖 (CLI Mode)")
    print("Type 'quit' to exit.")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye! 👋")
                break
            if not user_input:
                continue
                        
            print("🤖 Processing...")
            response = await chatbot.handle_message(user_input)
            # First, perform the replacement and store it in a new variable
            cli_response = response.replace('<br>', '\n') 
            # Then, print the new variable
            print(f"\nChatbot: {cli_response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main_cli())