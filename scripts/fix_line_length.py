#!/usr/bin/env python3
"""
Script to identify and fix line length issues in the codebase.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Configuration
MAX_LINE_LENGTH = 79
EXCLUDE_DIRS = {
    'venv', '__pycache__', '.git', '.pytest_cache', 'node_modules',
    'chroma_db', 'logs', 'scratch'
}
EXCLUDE_FILES = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin',
    '.log', '.txt', '.md', '.json', '.yaml', '.yml', '.toml',
    '.lock', '.sqlite', '.db'
}

def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped based on extension and location."""
    # Skip if in excluded directories
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return True

    # Skip if file extension is excluded
    if file_path.suffix.lower() in EXCLUDE_FILES:
        return True

    return False

def find_long_lines(root_dir: Path) -> List[Tuple[Path, int, str]]:
    """Find all lines longer than MAX_LINE_LENGTH."""
    long_lines = []

    for file_path in root_dir.rglob('*'):
        if file_path.is_file() and not should_skip_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if len(line.rstrip()) > MAX_LINE_LENGTH:
                            long_lines.append((file_path, line_num,
    line.rstrip()))
            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files we can't read
                continue

    return long_lines

def fix_python_file(file_path: Path) -> int:
    """Fix line length issues in a Python file."""
    fixes_applied = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fixed_lines = []
        for line in lines:
            original_line = line
            line = line.rstrip()

            if len(line) > MAX_LINE_LENGTH:
                # Try to fix common patterns
                fixed_line = fix_long_line(line)
                if fixed_line != line:
                    fixes_applied += 1
                    fixed_lines.append(fixed_line + '\n')
                else:
                    # If we can't fix it, keep original
                    fixed_lines.append(original_line)
            else:
                fixed_lines.append(original_line)

        # Write back if changes were made
        if fixes_applied > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            print(f"Fixed {fixes_applied} lines in {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return fixes_applied

def fix_long_line(line: str) -> str:
    """Attempt to fix a long line by breaking it appropriately."""
    # Remove trailing whitespace
    line = line.rstrip()

    # Skip if it's a comment or docstring that's too long
    if line.strip().startswith('#') or line.strip().startswith('"""') or \
    line.strip().startswith("'''"):
        return line

    # Skip if it's a long string literal
    if (line.count('"') > 1 and line.strip().startswith('"')) or \
       (line.count("'") > 1 and line.strip().startswith("'")):
        return line

    # Try to break at logical points
    if ' and ' in line:
        # Break at 'and' operators
        parts = line.split(' and ')
        if len(parts) > 1:
            result = parts[0]
            for part in parts[1:]:
                if len(result + ' and ' + part) <= MAX_LINE_LENGTH:
                    result += ' and ' + part
                else:
                    result += ' and \\\n    ' + part
            return result

    if ' or ' in line:
        # Break at 'or' operators
        parts = line.split(' or ')
        if len(parts) > 1:
            result = parts[0]
            for part in parts[1:]:
                if len(result + ' or ' + part) <= MAX_LINE_LENGTH:
                    result += ' or ' + part
                else:
                    result += ' or \\\n    ' + part
            return result

    if ' = ' in line and not line.strip().startswith('#'):
        # Break at assignment
        if ' = ' in line:
            before, after = line.split(' = ', 1)
            if len(before) < MAX_LINE_LENGTH - 10:
                return before + ' = \\\n    ' + after

    # Try to break at commas
    if ', ' in line:
        parts = line.split(', ')
        if len(parts) > 1:
            result = parts[0]
            for part in parts[1:]:
                if len(result + ', ' + part) <= MAX_LINE_LENGTH:
                    result += ', ' + part
                else:
                    result += ',\n    ' + part
            return result

    # If we can't fix it, return original
    return line

def main():
    """Main function to find and fix line length issues."""
    root_dir = Path('.')

    print("🔍 Scanning for line length issues...")
    long_lines = find_long_lines(root_dir)

    if not long_lines:
        print("✅ No line length issues found!")
        return

    print(f"📊 Found {len(long_lines)} lines longer than {MAX_LINE_LENGTH} characters")

    # Group by file
    files_with_issues = {}
    for file_path, line_num, line_content in long_lines:
        if file_path not in files_with_issues:
            files_with_issues[file_path] = []
        files_with_issues[file_path].append((line_num, line_content))

    print(f"📁 Issues found in {len(files_with_issues)} files:")
    for file_path in files_with_issues:
        print(f"  - {file_path} ({len(files_with_issues[file_path])} lines)")

    # Fix Python files
    total_fixes = 0
    for file_path in files_with_issues:
        if file_path.suffix == '.py':
            print(f"\n🔧 Fixing {file_path}...")
            fixes = fix_python_file(file_path)
            total_fixes += fixes

    print(f"\n✅ Applied {total_fixes} fixes to Python files")
    print("⚠️  Non-Python files need manual review")

if __name__ == "__main__":
    main()
