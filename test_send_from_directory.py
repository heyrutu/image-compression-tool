"""
Test script to verify send_from_directory parameters
"""
import inspect
from flask import send_from_directory

# Check the signature of send_from_directory
sig = inspect.signature(send_from_directory)
print("send_from_directory signature:")
print(f"  Parameters: {list(sig.parameters.keys())}")
print()

# Check the docstring
print("send_from_directory docstring:")
print(send_from_directory.__doc__)
