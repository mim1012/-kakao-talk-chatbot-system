"""
PyInstaller runtime hook to prevent paddlex import errors
"""
import sys
import os
import io

# Ensure stdout has buffer attribute (fix for PyInstaller)
if not hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')

# Prevent paddlex import
class FakePaddleX:
    """Dummy paddlex module to prevent import errors"""
    def __getattr__(self, name):
        return None
    
    class __version__:
        @staticmethod
        def __str__():
            return "0.0.0"

# Create fake paddlex module
sys.modules['paddlex'] = FakePaddleX()

# Also create a fake .version file attribute
class FakeVersion:
    def __init__(self):
        self.version = "0.0.0"
    
    def read(self):
        return "0.0.0"

# Monkey patch os.path.exists to return False for paddlex paths
original_exists = os.path.exists
def patched_exists(path):
    if 'paddlex' in str(path).lower():
        return False
    return original_exists(path)

os.path.exists = patched_exists

# Monkey patch open to handle paddlex/.version
original_open = open
def patched_open(file, *args, **kwargs):
    if 'paddlex' in str(file).lower() and '.version' in str(file).lower():
        # Return a fake file object
        import io
        return io.StringIO("0.0.0")
    return original_open(file, *args, **kwargs)

import builtins
builtins.open = patched_open