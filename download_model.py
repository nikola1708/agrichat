#!/usr/bin/env python3
"""Download Mistral 7B Q4_K model from Hugging Face"""

from huggingface_hub import snapshot_download
import os
import glob

print("📥 Downloading Mistral 7B Q4_K model...")
print("This may take 5-10 minutes depending on internet speed...\n")

try:
    model_dir = snapshot_download(
        repo_id="TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
        allow_patterns=["*.gguf"],
        local_dir="models",
        local_dir_use_symlinks=False
    )
    
    print(f"\n✓ Model downloaded successfully!")
    print(f"Location: {model_dir}\n")
    
    # Verify file exists
    gguf_files = glob.glob("models/**/*.gguf", recursive=True)
    if gguf_files:
        for f in gguf_files:
            size_mb = os.path.getsize(f) / (1024*1024)
            print(f"✓ {f} ({size_mb:.1f} MB)")
    else:
        print("⚠ No .gguf files found!")
        
except Exception as e:
    print(f"❌ Error downloading model: {e}")
    import traceback
    traceback.print_exc()
