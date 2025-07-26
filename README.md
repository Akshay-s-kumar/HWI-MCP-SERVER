# 🤖 MCP File System Assistant

A powerful natural language interface for file system operations using the Model Context Protocol (MCP). Talk to your computer's file system using plain English and let AI handle the complex operations for you.

## ✨ Features

### 🔍 **Intelligent File Search**
- **Lightning-fast indexed search** across your entire file system
- **Smart pattern matching** - find files by partial names, content, or patterns  
- **Natural language queries** - "find my latest resume" or "show Python files from last week"
- **Alias support** - use shortcuts like "desktop", "downloads", "documents"

### 📁 **Complete File Operations**
- **Read any text file** - supports 15+ file formats including code, configs, and documents
- **Create files with templates** - Python scripts, HTML pages, Markdown docs, and more
- **Smart editing** - write, append, or modify file contents
- **Safe operations** - confirmation prompts and rollback protection

### 🧠 **AI-Powered Intelligence**
- **Contextual understanding** - knows what you mean even with ambiguous requests
- **Multi-step operations** - "find my old project files and move them to archive"
- **Error recovery** - suggests fixes when operations fail
- **Learning conversation** - remembers context within your session

### 🛡️ **Enterprise-Grade Safety**
- **Protected directories** - prevents accidental system file deletion
- **Confirmation dialogs** - double-checks destructive operations
- **Detailed logging** - full audit trail of all operations
- **Graceful error handling** - never crashes, always recovers

## 🚀 Quick Start

### Option 1: Download Pre-Built Executable (Recommended)

1. **Download the latest release:**
   - Go to [Releases](https://github.com/yourusername/mcp-filesystem-assistant/releases)
   - Download `MCP-FileSystem-Assistant-Windows.zip`
   - Extract to any folder

2. **Get your free API key:**
   - Visit [console.groq.com](https://console.groq.com/)
   - Sign up (free, no credit card required)
   - Copy your API key

3. **Configure and run:**
   - Edit `config/.env` and paste your API key
   - Double-click `start.bat` or run `MCP-FileSystem-Assistant.exe`

### Option 2: Build from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-filesystem-assistant.git
cd mcp-filesystem-assistant

# Run setup (installs dependencies and creates config)
python setup.py

# Edit config/.env with your API key
# Then run the application
python launcher.py
```

## 💬 Usage Examples

### Basic File Operations
```
You: "Find all my Python files in the projects folder"
Assistant: Found 23 Python files. Here are the most recent ones:
           - /projects/web-scraper/main.py (modified 2 days ago)
           - /projects/data-analysis/processor.py (modified 1 week ago)
           ...

You: "Show me the contents of the main.py file"
Assistant: Here's the content of /projects/web-scraper/main.py:
           ```python
           import requests
           from bs4 import BeautifulSoup
           ...

You: "Create a new Python file called 'backup.py' with a basic template"
Assistant: Created /current-directory/backup.py with Python template:
           - Added shebang line and encoding
           - Included basic structure and imports
           - File is ready for editing
```

### Advanced Operations
```
You: "Find the latest version of my resume and move it to desktop"
Assistant: Found 3 resume files:
           1. resume_2024_final.pdf (Jan 15, 2024)
           2. resume_updated.docx (Jan 10, 2024)  
           3. old_resume.pdf (Dec 2023)
           
           Moving the latest version (resume_2024_final.pdf) to desktop...
           ✅ Successfully moved to C:\Users\You\Desktop\resume_2024_final.pdf

You: "Show me all large files over 100MB in my downloads, sorted by size"
Assistant: Found 7 files over 100MB in downloads:
           1. ubuntu-22.04.iso (3.6 GB)
           2. video_project_final.mp4 (850 MB)
           3. dataset_backup.zip (340 MB)
           ...
```

### Batch Operations
```
You: "Delete all .tmp files older than a week"
Assistant: Found 45 .tmp files older than 7 days.
           ⚠️  This will permanently delete 45 files (total: 2.3 GB)
           
           Continue? (y/n): y
           
           ✅ Deleted 45 temporary files, freed 2.3 GB of space
```

## 🏗️ Architecture

```
┌─────────────────┐    Natural Language    ┌─────────────────┐
│                 │───────────────────────▶│                 │
│  User Interface │                        │   AI Client     │
│   (Terminal)    │◀───────────────────────│  (Groq/OpenAI)  │
└─────────────────┘                        └─────────────────┘
                                                    │
                                           Tool Selection
                                                    │
                                                    ▼
┌─────────────────┐    MCP Protocol     ┌─────────────────────┐
│                 │◀────────────────────│                     │
│  File System    │                     │   MCP Server        │
│   Operations    │─────────────────────▶│  (Tool Provider)    │
└─────────────────┘                     └─────────────────────┘
```

The system uses the **Model Context Protocol (MCP)** to create a secure bridge between AI and your file system:

- **MCP Server**: Provides safe, sandboxed file operations
- **AI Client**: Interprets natural language and orchestrates operations  
- **User Interface**: Clean terminal-based interaction

## 🛠️ Available Tools

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `search_files` | Find files by name/pattern | "Find all .py files" |
| `find_latest_file` | Get most recent file matching pattern | "Latest resume in downloads" |
| `get_metadata` | Detailed file information | "Show info about large.zip" |
| `read_file` | Read text file contents | "Read config.json" |
| `create_file` | Create new file with templates | "Create Python script" |
| `write_file` | Write/overwrite file content | "Save this text to file" |
| `append_file` | Add content to existing file | "Add note to log file" |
| `delete_path` | Safely delete files/folders | "Delete old temp folder" |
| `move_file` | Move/rename files | "Move file to desktop" |
| `list_directory` | Show folder contents | "List files in documents" |
| `initialize_index` | Setup fast file indexing | "Index my directories" |

## ⚙️ Configuration

The application uses a `.env` file for configuration. Key settings:

```bash
# Required: Your Groq API key
GROQ_API_KEY=your_key_here

# AI Model Selection
DEFAULT_MODEL=llama3-70b-8192  # Most capable
# DEFAULT_MODEL=llama3-8b-8192   # Faster alternative

# File System Limits  
MAX_SEARCH_RESULTS=50
MAX_FILE_SIZE_MB=10

# Safety Settings
REQUIRE_DELETE_CONFIRMATION=true
PROTECTED_DIRECTORIES=C:\Windows,C:\Program Files

# Performance
AUTO_INDEX_ON_STARTUP=true
INDEX_DB_PATH=file_index.db
```

## 🏭 For Developers

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/yourusername/mcp-filesystem-assistant.git
cd mcp-filesystem-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with development settings
python launcher.py --debug
```

### Building Executables Locally

```bash
# Build for current platform
python build.py

# This creates:
# - dist/MCP-FileSystem-Assistant.exe (or platform equivalent)
# - MCP-FileSystem-Assistant-Windows.zip (portable package)
```

### Adding New Tools

1. **Define the tool in `server.py`:**
```python
@mcp.tool()
def my_custom_tool(param1: str, param2: int = 10):
    """Description of what this tool does."""
    # Your implementation here
    return {"result": "success", "data": "..."}
```

2. **Update the client's system prompt** to include the new tool
3. **Test with natural language**: "Use my custom tool with these parameters"

### Project Structure

```
mcp-filesystem-assistant/
├── 📄 server.py              # MCP server with file system tools
├── 📄 client.py              # AI-powered client application  
├── 📄 launcher.py            # Main executable entry point
├── 📄 setup.py               # Automated setup script
├── 📄 build.py               # Local build script
├── 🗂️ .github/workflows/     # GitHub Actions CI/CD
├── 🗂️ config/               # Configuration templates
├── 🗂️ examples/             # Usage examples and batch files
├── 🗂️ tests/                # Unit and integration tests
├── 🗂️ docs/                 # Documentation and guides
└── 📄 requirements.txt       # Python dependencies
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite**: `pytest`
5. **Submit a pull request**

### Areas We Need Help With

- 🌐 **Web interface** - Build a modern web UI
- 🐧 **Linux/macOS testing** - Ensure cross-platform compatibility
- 📚 **Documentation** - Improve guides and examples
- 🔌 **Integrations** - Cloud storage, version control, etc.
- 🧪 **Testing** - Expand test coverage
- 🔒 **Security** - Code audits and security enhancements

## 📊 GitHub Actions CI/CD

This project uses GitHub Actions for automated building and releasing:

### Automated Builds
- **Triggers**: Push to main, tags, pull requests
- **Platforms**: Windows, Linux, macOS
- **Outputs**: Native executables for each platform
- **Artifacts**: Portable packages ready for distribution

### Release Process
1. Create a new tag: `git tag v1.0.0 && git push origin v1.0.0`
2. GitHub Actions automatically:
   - Builds executables for all platforms
   - Runs tests and quality checks
   - Creates portable packages
   - Publishes a new GitHub release
3. Users can immediately download the latest version

### Build Configuration
The workflow is defined in `.github/workflows/build-and-release.yml` and includes:
- Dependency caching for faster builds
- Multi-platform compilation
- Automated testing
- Security scanning
- Release automation

## 📈 Performance

### Benchmarks
- **File search**: < 1 second for 100K+ indexed files
- **File operations**: Near-instant for files < 10MB
- **AI response**: 2-5 seconds depending on query complexity
- **Memory usage**: < 50MB for typical operations

### Optimization Tips
1. **Enable file indexing** - Run "initialize index" on first use
2. **Limit search scope** - Search specific folders instead of entire system
3. **Use specific queries** - "Python files in projects" vs "find files"
4. **Regular cleanup** - Remove old index files and logs periodically

## 🔒 Security & Privacy

### Data Protection
- **Local processing**: All file operations happen on your machine
- **API calls**: Only natural language queries sent to Groq (no file contents)
- **No data collection**: We don't store or transmit your files
- **Audit trail**: Complete logging of all operations

### Safety Features
- **Sandbox protection**: Cannot access system-critical directories
- **Confirmation prompts**: Double-check before destructive operations
- **Rollback capability**: Undo recent file operations
- **Permission respect**: Works within your user account limits

### Network Requirements
- **Internet needed for**: AI processing of natural language queries
- **Offline capability**: File operations work without internet
- **Minimal data usage**: Only text queries sent to API (< 1KB per request)

## 🐛 Troubleshooting

### Common Issues

**"GROQ_API_KEY not found"**
```bash
# Solution: Check your config file
cat config/.env
# Make sure it contains: GROQ_API_KEY=your_actual_key_here
```

**"Server connection failed"**
```bash
# Solution: Restart the application
# If using separate server/client:
python server.py  # Terminal 1
python client.py server.py  # Terminal 2
```

**"Permission denied" errors**
```bash
# Solution: Check file permissions
# Run as administrator if needed (Windows)
# Use sudo if needed (Linux/macOS) - not recommended for regular use
```

**Slow search performance**
```bash
# Solution: Initialize file index
# In the application, type: "initialize index for desktop and downloads"
```

### Debug Mode
```bash
# Run with debug output
python launcher.py --debug

# Or set in config/.env
DEBUG_MODE=true
```

### Log Files
Check `logs/mcp_assistant.log` for detailed error information.

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **RAM**: 2GB available memory
- **Storage**: 100MB free space
- **Network**: Internet connection for AI processing

### Recommended Requirements
- **OS**: Windows 11, macOS 12+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB+ available memory
- **Storage**: 1GB free space (for indexing large file systems)
- **Network**: Broadband internet for responsive AI processing

### Supported File Types
**Read/Write Support:**
- Text: `.txt`, `.md`, `.log`
- Code: `.py`, `.js`, `.html`, `.css`, `.sql`
- Config: `.json`, `.xml`, `.yml`, `.ini`, `.cfg`
- Scripts: `.sh`, `.bat`, `.ps1`

**Metadata Support:**
- All file types (size, dates, permissions)

## 🗺️ Roadmap

### Version 1.1 (Next Release)
- [ ] **Web Interface** - Browser-based GUI
- [ ] **Cloud Integration** - Google Drive, Dropbox, OneDrive
- [ ] **Advanced Search** - Content search, file similarity
- [ ] **Batch Operations** - Process multiple files at once

### Version 1.2 (Future)
- [ ] **Plugin System** - Custom tool development
- [ ] **Team Features** - Shared configurations and scripts
- [ ] **API Access** - REST API for integration
- [ ] **Mobile App** - iOS and Android companion

### Version 2.0 (Long-term)
- [ ] **Local AI Models** - Run without internet
- [ ] **Visual Interface** - GUI application
- [ ] **Advanced Analytics** - File usage patterns and insights
- [ ] **Enterprise Features** - SSO, audit logs, compliance

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 MCP File System Assistant Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **[Model Context Protocol](https://modelcontextprotocol.io/)** - The foundation that makes this possible
- **[Groq](https://groq.com/)** - Lightning-fast AI inference
- **[PyInstaller](https://pyinstaller.org/)** - Python to executable conversion
- **[GitHub Actions](https://github.com/features/actions)** - Automated CI/CD pipeline

## 📞 Support

- **📖 Documentation**: [GitHub Wiki](https://github.com/yourusername/mcp-filesystem-assistant/wiki)
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/yourusername/mcp-filesystem-assistant/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/yourusername/mcp-filesystem-assistant/discussions)
- **💬 Community**: [Discord Server](https://discord.gg/mcp-filesystem)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/mcp-filesystem-assistant&type=Date)](https://star-history.com/#yourusername/mcp-filesystem-assistant&Date)

---

<div align="center">

**[⬆ Back to Top](#-mcp-file-system-assistant)**

Made with ❤️ by the MCP File System Assistant team

[![GitHub stars](https://img.shields.io/github/stars/yourusername/mcp-filesystem-assistant?style=social)](https://github.com/yourusername/mcp-filesystem-assistant/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/mcp-filesystem-assistant?style=social)](https://github.com/yourusername/mcp-filesystem-assistant/network/members)

</div>