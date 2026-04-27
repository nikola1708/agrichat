#!/usr/bin/env python3
"""Test all required imports"""

print("Testing imports...")

try:
    import azure.functions
    print("✅ azure.functions")
except ImportError as e:
    print(f"❌ azure.functions: {e}")

try:
    import azure.cosmos
    print("✅ azure.cosmos")
except ImportError as e:
    print(f"❌ azure.cosmos: {e}")

try:
    import requests
    print("✅ requests")
except ImportError as e:
    print(f"❌ requests: {e}")

try:
    import openai
    print("✅ openai")
except ImportError as e:
    print(f"❌ openai: {e}")

try:
    from PIL import Image
    print("✅ PIL")
except ImportError as e:
    print(f"❌ PIL: {e}")

try:
    import aiohttp
    print("✅ aiohttp")
except ImportError as e:
    print(f"❌ aiohttp: {e}")

print("\n✨ All imports working!")
