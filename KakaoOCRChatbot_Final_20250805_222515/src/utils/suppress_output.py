"""
Utility to suppress stdout/stderr output
"""
import sys
import os
import contextlib
import io

class SuppressOutput:
    """Context manager to suppress all output"""
    
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._null = open(os.devnull, 'w', encoding='utf-8')
        sys.stdout = self._null
        sys.stderr = self._null
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        self._null.close()

@contextlib.contextmanager
def suppress_stdout_stderr():
    """Context manager that suppresses stdout and stderr"""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        with open(os.devnull, 'w', encoding='utf-8') as devnull:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr