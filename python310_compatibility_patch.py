#!/usr/bin/env python3
"""
Python 3.10 Compatibility Patch for A2A Double Validation

This script patches the common/types.py file to make it compatible with Python 3.10
by replacing the 'Self' import from typing with a fallback to typing_extensions.

Run this script once after cloning the repository if you're using Python 3.10.
"""

import os
import sys

def patch_types_file():
    """Patch the common/types.py file for Python 3.10 compatibility."""
    
    types_file_path = "common/types.py"
    
    if not os.path.exists(types_file_path):
        print(f"Error: {types_file_path} not found. Make sure you're running this from the project root.")
        return False
    
    # Read the current content
    with open(types_file_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if "try:" in content and "from typing_extensions import Self" in content:
        print("File is already patched for Python 3.10 compatibility.")
        return True
    
    # Apply the patch
    old_import = "from typing import Annotated, Any, Literal, Self"
    new_import = """from typing import Annotated, Any, Literal

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self"""
    
    if old_import in content:
        patched_content = content.replace(old_import, new_import)
        
        # Write the patched content back
        with open(types_file_path, 'w') as f:
            f.write(patched_content)
        
        print("Successfully patched common/types.py for Python 3.10 compatibility.")
        return True
    else:
        print("Warning: Expected import pattern not found. The file may have been modified.")
        print("Please manually update the import in common/types.py:")
        print("Replace:")
        print("  from typing import Annotated, Any, Literal, Self")
        print("With:")
        print("  from typing import Annotated, Any, Literal")
        print("  try:")
        print("      from typing import Self")
        print("  except ImportError:")
        print("      from typing_extensions import Self")
        return False

if __name__ == "__main__":
    print("A2A Double Validation - Python 3.10 Compatibility Patch")
    print("=" * 55)
    
    # Check Python version
    if sys.version_info >= (3, 11):
        print("You're running Python 3.11+. This patch is not needed.")
        print("However, applying it won't cause any issues.")
    elif sys.version_info < (3, 10):
        print("Warning: This project requires Python 3.10+")
        print(f"You're running Python {sys.version_info.major}.{sys.version_info.minor}")
    
    success = patch_types_file()
    
    if success:
        print("\nYou can now run the application with:")
        print("  python main.py")
    else:
        print("\nPatch failed. Please apply the changes manually.")
    
    sys.exit(0 if success else 1) 