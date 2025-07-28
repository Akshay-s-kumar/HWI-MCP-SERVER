from fastmcp import FastMCP 
from pathlib import Path
from datetime import datetime
import shutil
import os
import json
import sqlite3
import threading
import time
from typing import List, Dict, Any

mcp = FastMCP("FileSystemMCPServer")

class FileIndexer:
    """File indexing system for fast search operations"""
    
    def __init__(self, db_path: str = "file_index.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for file indexing"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE,
                    name TEXT,
                    size INTEGER,
                    created REAL,
                    modified REAL,
                    type TEXT,
                    indexed_at REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON files(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON files(path)")
    
    def index_directory(self, base_path: Path, progress_callback=None):
        """Index all files in a directory recursively"""
        files_processed = 0
        with sqlite3.connect(self.db_path) as conn:
            for file_path in base_path.rglob("*"):
                try:
                    if file_path.is_file():
                        stat = file_path.stat()
                        conn.execute("""
                            INSERT OR REPLACE INTO files 
                            (path, name, size, created, modified, type, indexed_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(file_path.resolve()),
                            file_path.name,
                            stat.st_size,
                            stat.st_ctime,
                            stat.st_mtime,
                            file_path.suffix.lower(),
                            time.time()
                        ))
                        files_processed += 1
                        if progress_callback and files_processed % 100 == 0:
                            progress_callback(files_processed)
                except (OSError, PermissionError):
                    continue
        return files_processed
    
    def search_files(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search indexed files by name"""
        with open("logs.txt", "a") as w:
            w.write("Searching for: " + query)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT path, name, size, created, modified, type 
                FROM files 
                WHERE name LIKE ? 
                ORDER BY modified DESC 
                LIMIT ?
            """, (f"%{query}%", limit))
            with open("logs.txt", "a") as w:
                w.write("connected")
                results = []
            for row in cursor.fetchall():
                results.append({
                    "path": row[0],
                    "name": row[1],
                    "size": row[2],
                    "created": datetime.fromtimestamp(row[3]).isoformat(),
                    "modified": datetime.fromtimestamp(row[4]).isoformat(),
                    "type": row[5]
                })
            with open("logs.txt", "a") as w:
                json.dump(results, w)
            return results

# Global file indexer
indexer = FileIndexer()

def resolve_path(file_path: str) -> Path:
    """Resolve aliases like 'desktop', 'downloads' to real absolute paths."""
    aliases = {
        "desktop": Path.home() / "Desktop",
        "downloads": Path.home() / "Downloads", 
        "documents": Path.home() / "Documents",
        "pictures": Path.home() / "Pictures",
        "videos": Path.home() / "Videos",
        "music": Path.home() / "Music"
    }

    parts = Path(file_path).parts
    if parts and parts[0].lower() in aliases:
        base = aliases[parts[0].lower()]
        remaining = Path(*parts[1:]) if len(parts) > 1 else Path()
        return (base / remaining).expanduser().resolve()
    else:
        return Path(file_path).expanduser().resolve()

# Initialize file index
@mcp.tool()
def initialize_index(directories: str = "desktop,downloads,documents"):
    """Initialize file indexing for faster searches. Run this once on first setup."""
    try:
        dir_list = [d.strip() for d in directories.split(",")]
        total_files = 0
        
        for dir_name in dir_list:
            dir_path = resolve_path(dir_name)
            if dir_path.exists():
                files_count = indexer.index_directory(dir_path)
                total_files += files_count
        
        return {
            "status": "success",
            "message": f"Indexed {total_files} files from {len(dir_list)} directories",
            "directories_indexed": dir_list
        }
    except Exception as e:
        return {"error": f"Failed to initialize index: {str(e)}"}

# Enhanced search with indexing
@mcp.tool()
def search_files(query: str, search_path: str = "all", use_index: bool = True):
    """Search for files or folders matching the query string with optional indexing."""
    if use_index:
        try:
            results = indexer.search_files(query)
            if results:
                return {
                    "matches": [r["path"] for r in results],
                    "detailed_results": results,
                    "count": len(results),
                    "search_method": "indexed"
                }
        except Exception:
            pass  # Fall back to filesystem search
    
    # Fallback to filesystem search
    default_dirs = {
        "desktop": Path.home() / "Desktop",
        "downloads": Path.home() / "Downloads",
        "documents": Path.home() / "Documents",
        "pictures": Path.home() / "Pictures",
        "videos": Path.home() / "Videos",
        "music": Path.home() / "Music"
    }

    if search_path.lower() == "all":
        base_paths = list(default_dirs.values())
    elif search_path.strip().lower() in default_dirs:
        base_paths = [default_dirs[search_path.strip().lower()]]
    else:
        base_path = resolve_path(search_path)
        base_paths = [base_path] if base_path.exists() else list(default_dirs.values())

    matches = []
    detailed_results = []
    
    for base in base_paths:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if query.lower() in path.name.lower():
                matches.append(str(path.resolve()))
                if path.is_file():
                    stat = path.stat()
                    detailed_results.append({
                        "path": str(path.resolve()),
                        "name": path.name,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": path.suffix.lower()
                    })
                if len(matches) >= 50:
                    break
        if len(matches) >= 50:
            break

    return {
        "matches": matches,
        "detailed_results": detailed_results,
        "count": len(matches),
        "search_method": "filesystem"
    }

#  Find latest file by pattern
@mcp.tool()
def find_latest_file(pattern: str, search_path: str = "downloads"):
    """Find the most recently modified file matching a pattern."""
    search_result = search_files(pattern, search_path)
    
    if not search_result["detailed_results"]:
        return {"error": f"No files found matching pattern '{pattern}'"}
    
    # Sort by modification time (most recent first)
    sorted_files = sorted(
        search_result["detailed_results"],
        key=lambda x: x["modified"],
        reverse=True
    )
    
    return {
        "latest_file": sorted_files[0],
        "all_matches": sorted_files,
        "pattern": pattern
    }

# Enhanced metadata with permissions
@mcp.tool()
def get_metadata(file_path: str):
    """Return comprehensive file or directory metadata."""
    path = resolve_path(file_path)
    if not path.exists():
        return {"error": "Path not found"}

    try:
        stat = path.stat()
        metadata = {
            "path": str(path.resolve()),
            "name": path.name,
            "size": stat.st_size,
            "size_human": format_file_size(stat.st_size),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "type": "directory" if path.is_dir() else "file",
            "extension": path.suffix.lower() if path.is_file() else None,
            "permissions": oct(stat.st_mode)[-3:],
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
            "executable": os.access(path, os.X_OK)
        }
        
        if path.is_dir():
            try:
                contents = list(path.iterdir())
                metadata["contents_count"] = len(contents)
                metadata["subdirectories"] = sum(1 for p in contents if p.is_dir())
                metadata["files"] = sum(1 for p in contents if p.is_file())
            except PermissionError:
                metadata["contents_count"] = "Permission denied"
        
        return metadata
    except Exception as e:
        return {"error": f"Failed to get metadata: {str(e)}"}

def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

# 📖 Enhanced file reading with encoding detection
@mcp.tool()
def read_file(file_path: str, max_chars: int = 5000):
    """Read content from various file types with encoding detection."""
    path = resolve_path(file_path)
    if not path.exists() or not path.is_file():
        return {"error": "File not found or not a file."}
    
    # Supported text file extensions
    text_extensions = {'.txt', '.md', '.py', '.csv', '.json', '.xml', '.html', '.css', '.js', 
                      '.log', '.cfg', '.ini', '.yml', '.yaml', '.sql', '.sh', '.bat'}
    
    if path.suffix.lower() not in text_extensions:
        return {"error": f"Unsupported file type: {path.suffix}. Supported types: {', '.join(text_extensions)}"}
    
    try:
        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        content = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    content = f.read()
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return {"error": "Could not decode file with any supported encoding"}
        
        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars] + f"\n... [Content truncated. Total length: {len(content)} chars]"
        
        return {
            "path": str(path.resolve()),
            "content": content,
            "encoding": used_encoding,
            "truncated": truncated,
            "size": path.stat().st_size
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

# ✍️ Create new file with templates
@mcp.tool()
def create_file(file_path: str, content: str = "", template: str = None):
    """Create a new file with optional template."""
    path = resolve_path(file_path)
    
    if path.exists():
        return {"error": f"File already exists: {str(path)}"}
    
    templates = {
        "python": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\nPython script template\n\"\"\"\n\n",
        "html": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Document</title>\n</head>\n<body>\n\n</body>\n</html>",
        "markdown": "# Title\n\n## Description\n\nContent goes here...\n",
        "json": "{\n    \"example\": \"value\"\n}",
        "csv": "column1,column2,column3\n"
    }
    
    final_content = content
    if template and template.lower() in templates:
        final_content = templates[template.lower()] + content
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(final_content)
        return {
            "status": "created",
            "path": str(path.resolve()),
            "template_used": template,
            "size": len(final_content)
        }
    except Exception as e:
        return {"error": f"Failed to create file: {str(e)}"}

# ✏️ Write/overwrite file
@mcp.tool()
def write_file(file_path: str, content: str):
    """Write or overwrite file content."""
    path = resolve_path(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "status": "written",
            "path": str(path.resolve()),
            "size": len(content)
        }
    except Exception as e:
        return {"error": f"Failed to write file: {str(e)}"}

# ➕ Append to file
@mcp.tool()
def append_file(file_path: str, content: str, newline: bool = True):
    """Append content to an existing file."""
    path = resolve_path(file_path)
    
    if not path.exists():
        return {"error": "File does not exist. Use create_file or write_file instead."}
    
    try:
        with open(path, "a", encoding="utf-8") as f:
            if newline and not content.startswith('\n'):
                f.write('\n')
            f.write(content)
        
        new_size = path.stat().st_size
        return {
            "status": "appended",
            "path": str(path.resolve()),
            "appended_length": len(content),
            "new_file_size": new_size
        }
    except Exception as e:
        return {"error": f"Failed to append to file: {str(e)}"}

# ❌ Delete with safety checks
@mcp.tool()
def delete_path(file_path: str, confirm: bool = False):
    """Delete file or folder with safety checks. Set confirm=True to actually delete."""
    path = resolve_path(file_path)
    
    # Safety checks
    critical_paths = ["/", str(Path.home().anchor), str(Path.home()), "/Windows", "/System32"]
    if str(path.resolve()) in critical_paths or len(str(path)) < 4:
        return {"error": "Deletion of critical system paths is not allowed."}
    
    if not path.exists():
        return {"error": "Path not found."}
    
    if not confirm:
        item_type = "directory" if path.is_dir() else "file"
        size_info = ""
        if path.is_file():
            size_info = f" (size: {format_file_size(path.stat().st_size)})"
        elif path.is_dir():
            try:
                contents = list(path.rglob("*"))
                size_info = f" (contains {len(contents)} items)"
            except:
                size_info = " (contents unknown)"
        
        return {
            "status": "confirmation_required",
            "message": f"Are you sure you want to delete this {item_type}?",
            "path": str(path.resolve()),
            "type": item_type,
            "info": size_info,
            "instruction": "Call delete_path again with confirm=True to proceed"
        }
    
    try:
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        return {
            "status": "deleted",
            "deleted_path": str(path.resolve())
        }
    except Exception as e:
        return {"error": f"Failed to delete: {str(e)}"}

# 🔁 Enhanced move/rename with conflict handling
@mcp.tool()
def move_file(src: str, dest: str, overwrite: bool = False):
    """Move or rename a file or folder with conflict handling."""
    src_path = resolve_path(src)
    dest_path = resolve_path(dest)
    
    if not src_path.exists():
        return {"error": "Source path does not exist."}
    
    if dest_path.exists() and not overwrite:
        return {
            "error": "Destination already exists.",
            "suggestion": "Set overwrite=True to replace, or choose a different destination.",
            "existing_dest": str(dest_path.resolve())
        }
    
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if dest_path.exists() and overwrite:
            if dest_path.is_file():
                dest_path.unlink()
            else:
                shutil.rmtree(dest_path)
        
        shutil.move(str(src_path), str(dest_path))
        return {
            "status": "moved",
            "from": str(src_path.resolve()),
            "to": str(dest_path.resolve()),
            "overwritten": overwrite and dest_path.exists()
        }
    except Exception as e:
        return {"error": f"Failed to move or rename: {str(e)}"}

# 📁 List directory contents
@mcp.tool()
def list_directory(dir_path: str = ".", include_hidden: bool = False, sort_by: str = "name"):
    """List contents of a directory with sorting options."""
    path = resolve_path(dir_path)
    
    if not path.exists():
        return {"error": "Directory not found."}
    
    if not path.is_dir():
        return {"error": "Path is not a directory."}
    
    try:
        items = []
        for item in path.iterdir():
            if not include_hidden and item.name.startswith('.'):
                continue
            
            try:
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item.resolve()),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "size_human": format_file_size(stat.st_size) if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": item.suffix.lower() if item.is_file() else None
                })
            except (OSError, PermissionError):
                continue
        # Sort items
        sort_keys = {
            "name": lambda x: x["name"].lower(),
            "size": lambda x: x["size"] or 0,
            "modified": lambda x: x["modified"],
            "type": lambda x: (x["type"], x["name"].lower())
        }
        
        if sort_by in sort_keys:
            items.sort(key=sort_keys[sort_by])
        
        return {
            "directory": str(path.resolve()),
            "items": items,
            "count": len(items),
            "sorted_by": sort_by
        }
    except Exception as e:
        return {"error": f"Failed to list directory: {str(e)}"}

# 🚀 Start MCP
if __name__ == "__main__":
    mcp.run()