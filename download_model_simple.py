#!/usr/bin/env python3
"""Simple model downloader using requests"""

import os
import requests
from pathlib import Path

# Model details
REPO_ID = "TheBloke/Mistral-7B-Instruct-v0.1-GGUF"
MODEL_FILE = "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
MODEL_URL = f"https://huggingface.co/{REPO_ID}/resolve/main/{MODEL_FILE}"

# Setup
models_dir = Path("models")
models_dir.mkdir(exist_ok=True)
model_path = models_dir / MODEL_FILE

print(f"📥 Downloading {MODEL_FILE}...")
print(f"URL: {MODEL_URL}")
print(f"Target: {model_path}")
print()

# Check if already exists
if model_path.exists():
    size_gb = model_path.stat().st_size / (1024**3)
    print(f"✓ Model sudah ada: {size_gb:.2f} GB")
    print(f"Path: {model_path.absolute()}")
    exit(0)

try:
    # Download with progress
    response = requests.get(MODEL_URL, stream=True, timeout=300)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    total_size_gb = total_size / (1024**3)
    
    print(f"Size: {total_size_gb:.2f} GB")
    print(f"Starting download... (ini mungkin butuh 10-30 menit)\n")
    
    downloaded = 0
    with open(model_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                
                # Progress
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    downloaded_gb = downloaded / (1024**3)
                    print(f"\r Progress: {percent:.1f}% ({downloaded_gb:.2f}/{total_size_gb:.2f} GB)", end='', flush=True)
    
    print("\n")
    final_size_gb = model_path.stat().st_size / (1024**3)
    print(f"✓ Download selesai!")
    print(f"Path: {model_path.absolute()}")
    print(f"Size: {final_size_gb:.2f} GB")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if model_path.exists():
        model_path.unlink()
    exit(1)
