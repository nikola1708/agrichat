#!/usr/bin/env python3
"""Download model using urllib (built-in, no dependencies)"""

import urllib.request
import os
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
print(f"Target: {model_path}")
print("(This will take 30-60 minutes depending on internet speed)\n")

# Check if already exists
if model_path.exists():
    size_gb = model_path.stat().st_size / (1024**3)
    print(f"✓ Model sudah ada: {size_gb:.2f} GB")
    print(f"Path: {model_path.absolute()}")
    exit(0)

try:
    # Simple download with progress
    def reporthook(blocknum, blocksize, totalsize):
        downloaded = blocknum * blocksize
        if totalsize > 0:
            percent = (downloaded / totalsize) * 100
            downloaded_gb = downloaded / (1024**3)
            total_gb = totalsize / (1024**3)
            mb_per_sec = (downloaded / (1024**2)) / max(1, blocknum)
            print(f"\rProgress: {percent:.1f}% ({downloaded_gb:.2f}/{total_gb:.2f} GB) - {mb_per_sec:.1f} MB/s", end='', flush=True)
    
    urllib.request.urlretrieve(MODEL_URL, model_path, reporthook)
    
    print("\n")
    final_size_gb = model_path.stat().st_size / (1024**3)
    print(f"✓ Download selesai!")
    print(f"Path: {model_path.absolute()}")
    print(f"Size: {final_size_gb:.2f} GB")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    if model_path.exists():
        model_path.unlink()
    exit(1)
