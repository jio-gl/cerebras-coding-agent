import os
from pathlib import Path
from typing import List, Set, Optional
import fnmatch
from gitignore_parser import parse_gitignore

class FileOperations:
    def __init__(self, root_path: str):
        """Initialize file operations with a root path.
        
        Args:
            root_path: The root directory to operate in
        """
        self.root_path = Path(os.path.abspath(root_path))
        print(f"📁 FileOperations initialized with root path: {self.root_path}")
        self._gitignore_patterns: Optional[Set[str]] = None
        self._load_gitignore()
    
    def _load_gitignore(self):
        """Load .gitignore patterns if they exist."""
        gitignore_path = self.root_path / '.gitignore'
        try:
            if gitignore_path.exists():
                self._gitignore_patterns = parse_gitignore(str(gitignore_path))
            else:
                self._gitignore_patterns = set()
        except Exception:
            self._gitignore_patterns = set()
    
    def is_ignored(self, path: str) -> bool:
        """Check if a path should be ignored based on .gitignore patterns.
        
        Args:
            path: The path to check
            
        Returns:
            bool: True if the path should be ignored
        """
        try:
            # Convert to absolute path if relative
            path = Path(path)
            if not path.is_absolute():
                path = self.root_path / path
            rel_path = path.relative_to(self.root_path)
            if callable(self._gitignore_patterns):
                return self._gitignore_patterns(str(rel_path))
            elif isinstance(self._gitignore_patterns, set):
                # If no .gitignore, treat as not ignored
                return False
            else:
                return False
        except ValueError:
            # If path is not relative to repo_path, it's not in the repo
            return True
    
    def find_files(self, pattern: str = "*", include_ignored: bool = False, file_types: List[str] = None) -> List[str]:
        """Find files in the repository matching the given pattern and file types."""
        if not self.root_path:
            return []

        found_files = []
        for path in self.root_path.rglob(pattern):
            if not path.is_file():
                continue
                
            rel_path = path.relative_to(self.root_path)
            
            # Skip ignored files unless explicitly included
            if not include_ignored and self.is_ignored(str(rel_path)):
                continue
                
            # Check file type if specified
            if file_types:
                if not any(str(rel_path).endswith(ft) for ft in file_types):
                    continue
                    
            found_files.append(str(rel_path))
                
        return found_files
    
    def grep_files(self, 
                  pattern: str,
                  include_ignored: bool = False,
                  file_types: Optional[List[str]] = None) -> List[tuple]:
        """Search for a pattern in files, respecting .gitignore.
        
        Args:
            pattern: The pattern to search for
            include_ignored: Whether to include ignored files
            file_types: List of file extensions to include
            
        Returns:
            List of tuples (file_path, line_number, line_content)
        """
        matches = []
        
        for file_path in self.find_files(include_ignored=include_ignored, file_types=file_types):
            full_path = self.root_path / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if pattern in line:
                            matches.append((file_path, i, line.strip()))
            except (UnicodeDecodeError, IOError):
                # Skip binary files or files we can't read
                continue
        
        return matches
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get the content of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string, or None if file can't be read
        """
        # Convert to absolute path if relative
        path = Path(file_path)
        if not path.is_absolute():
            path = self.root_path / path
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except (UnicodeDecodeError, IOError):
            return None
    
    def get_repository_structure(self) -> dict:
        """Get the structure of the repository as a dictionary.
        
        Returns:
            Dictionary representing the repository structure
        """
        structure = {}
        
        # First add the root directory
        for item in self.root_path.iterdir():
            rel_path = item.relative_to(self.root_path)
            
            # Skip ignored files and directories
            if self.is_ignored(str(rel_path)):
                continue
                
            if item.is_dir():
                structure[item.name] = {}
            else:
                structure[item.name] = None
        
        # Then recursively add subdirectories
        for path in self.root_path.rglob("*"):
            if not path.is_dir():
                continue
                
            # Skip ignored directories
            rel_path = path.relative_to(self.root_path)
            if self.is_ignored(str(rel_path)):
                continue
            
            # Navigate to the correct position in the structure
            parts = str(rel_path).split(os.sep)
            current = structure
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Add files in this directory
            for file_path in path.iterdir():
                if not file_path.is_file():
                    continue
                    
                file_rel_path = file_path.relative_to(self.root_path)
                if self.is_ignored(str(file_rel_path)):
                    continue
                    
                current[file_path.name] = None
        
        return structure 