# QUICK START: Jalankan Llama.cpp dalam 5 Menit

**Goal**: Setup dan test model llama.cpp lokal untuk respons cepat.

## 1️⃣ Install Dependencies (2 menit)

```bash
cd c:\project\agrichat
.venv\Scripts\activate

# Install packages (including llama-cpp-python)
pip install -r requirements.txt
```

Jika ada error:
```bash
pip install --upgrade pip
pip install llama-cpp-python==0.2.90 --prefer-binary
```

## 2️⃣ Download Model (3 menit atau lebih sesuai internet speed)

```bash
# Install downloader
pip install huggingface-hub

# Buat folder models
mkdir models
cd models

# Download Mistral 7B Q4 (recommended, 1.5 GB)
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.1-GGUF ^
  mistral-7b-instruct-v0.1.Q4_K_M.gguf ^
  --local-dir . --local-dir-use-symlinks False
```

**Selesai download?** Lanjut ke step 3.

## 3️⃣ Setup Environment Variables (1 menit)

Buka `local.settings.json` dan pastikan ini ada:

```json
"AI_ENGINE": "llamacpp",
"LLAMACPP_MODEL_PATH": "C:\\project\\agrichat\\models\\mistral-7b-instruct-v0.1.Q4_K_M.gguf",
"LLAMACPP_N_CTX": "512",
"LLAMACPP_N_THREADS": "4",
"LLAMACPP_N_GPU_LAYERS": "0"
```

**Windows path**: Gunakan `\\` (double backslash)  
**Linux/Mac path**: Gunakan `/`

## 4️⃣ Test Model (1-2 menit untuk first run)

```bash
# Aktifkan venv
.venv\Scripts\activate

# Test 1: Import check
python -c "from llama_cpp import Llama; print('✓ llama-cpp-python OK')"

# Test 2: Model loading & inference (first run = slow, next run = fast)
python -c "
from shared.ai_engine import get_ai_engine
engine = get_ai_engine()
print('Testing inference...')
response = engine.generate_response('user123', 'Apakah bisa tanam padi di musim kering?')
print('Response:', response)
"
```

**First run**: ~30-60 detik (model loading)  
**Subsequent runs**: 2-5 detik per response

## 5️⃣ Build FAISS Index (Optional tapi recommended)

```bash
# Hapus index lama (jika ada)
del .faiss_index .faiss_metadata.json 2>nul

# Build index baru
python shared/build_faiss_index.py --src docs

# Output:
# INFO:root:Built FAISS index with XX documents
```

## 6️⃣ Run Telegram Bot

```bash
# Start Azure Functions (backend)
func start

# Atau run directly
python telegram_webhook/function_app.py
```

**Expected**: Bot responds to Telegram dalam 2-5 detik!

---

## ✅ Troubleshooting

### ❌ Error: "ModuleNotFoundError: No module named 'llama_cpp'"
```bash
pip install llama-cpp-python==0.2.90 --prefer-binary
```

### ❌ Error: "LLAMACPP_MODEL_PATH not found"
1. Pastikan path **absolute** (bukan relative)
2. Gunakan `\\` di Windows: `C:\\project\\agrichat\\models\\...`
3. File harus exist: `ls models/mistral*.gguf`

### ❌ Slow Response (>30 detik)
1. Reduce context: `LLAMACPP_N_CTX=256` (dari 512)
2. Check threads: `LLAMACPP_N_THREADS=2` (lebih cepat, less accurate)
3. Try smaller model: Download Phi-2 (2.7B, lebih ringan)

### ❌ Out of Memory
1. Reduce context: `LLAMACPP_N_CTX=256`
2. Close background apps
3. Use smaller model (Phi-2 2.7B instead of Mistral 7B)

### ❌ Response kualitas jelek
→ Model butuh "warming up" (pertama kali cukup lambat)  
→ Coba question yg lebih jelas  
→ Check prompt quality (lihat ai_engine.py)

---

## 📊 Expected Performance

```
Question: "Apakah cocok tanam padi sekarang?"
Response time: 2-5 seconds (setelah model loaded)
Quality: Good (comparable dengan GPT-3.5)
Offline: Yes (fully local)
Cost: $0 (gratis!)
```

---

## 🎯 Next Steps

✅ **Setelah ini berhasil:**
1. Test dengan beberapa pertanyaan via Telegram
2. Fine-tune prompts di `shared/ai_engine.py` untuk hasil lebih baik
3. Build FAISS index untuk knowledge base yang lebih rich
4. (Optional) Switch ke Ollama untuk model management yang lebih mudah

✅ **Production checklist:**
- [ ] Model loaded & responding <10 seconds
- [ ] FAISS index built
- [ ] Telegram bot integrated
- [ ] Monitor response quality

---

**Total setup time**: 10-15 menit  
**Monthly cost**: FREE  
**Latency**: 2-5 seconds (vs 5+ minutes sebelumnya)  
**Status**: Ready for POC & prototype! 🚀
