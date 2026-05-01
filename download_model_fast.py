#!/usr/bin/env python3
"""Download ONLY Mistral Q4_K_M model (efficient single file download)"""

from huggingface_hub import hf_hub_download
import os

print("📥 Downloading ONLY Mistral 7B Q4_K_M model...")
print("Single file download (~1.5 GB)...\n")

try:
    # Make sure models dir exists
    os.makedirs('models', exist_ok=True)
    
    # Download ONLY the Q4_K_M variant (the one we need)
    model_path = hf_hub_download(
        repo_id="TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
        filename="mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        local_dir="models"
    )
    
    print(f"\n✓ Model downloaded successfully!")
    print(f"Path: {model_path}")
    
    # Check file size
    file_size_gb = os.path.getsize(model_path) / (1024**3)
    print(f"Size: {file_size_gb:.2f} GB")
    
    # Verify it's what we need
    if "Q4_K_M" in model_path:
        print("✓ Correct model variant (Q4_K_M)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
