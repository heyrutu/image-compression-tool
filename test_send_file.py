"""
Test script to check send_file parameters
"""
import inspect
from flask import send_file

# Check the signature of send_file
sig = inspect.signature(send_file)
print("send_file signature:")
print(f"  Parameters: {list(sig.parameters.keys())}")
print()

# Check the docstring
print("send_file docstring:")
print(send_file.__doc__[:1500])
