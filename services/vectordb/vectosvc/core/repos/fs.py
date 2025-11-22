from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from .base import BlobRepository


class LocalFSRepository(BlobRepository):
    def read(self, uri: str) -> bytes:
        # Accept file:// URIs or bare paths
        if uri.startswith("file://"):
            # Parse the file:// URL and decode URL-encoded characters (%20, etc.)
            parsed = urlparse(uri)
            path_str = unquote(parsed.path)
            
            # Handle relative paths (file://path/to/file) vs absolute (file:///path/to/file)
            # If path doesn't start with /, it's relative
            if path_str and not path_str.startswith('/'):
                # Relative path - resolve from current working directory
                path = Path.cwd() / path_str
            else:
                path = Path(path_str).expanduser()
        else:
            # Plain path (relative or absolute)
            path = Path(uri)
            # If it's relative, resolve from cwd
            if not path.is_absolute():
                path = Path.cwd() / path
            path = path.expanduser()
        
        if not path.exists():
            raise FileNotFoundError(f"Local file not found: {uri}")
        return path.read_bytes()

