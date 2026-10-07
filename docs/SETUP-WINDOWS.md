# Windows Setup — AIOS Runtime

## 1. Install Node.js

Install a current LTS release. Verify:

```powershell
node -v
npm -v
```

## 2. Install Python

```powershell
py -3.13 --version
```

Create environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3. Install dependencies

```powershell
npm install
cd apps/web
npm install
cd ../..
```

## 4. Start

Terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/run_api.py
```

Terminal 2:

```powershell
npm --prefix apps/web run dev
```

Open `http://localhost:3000`.

## 5. Ollama

Install Ollama, then:

```powershell
ollama pull gemma3:4b
```

If your machine cannot comfortably run that model, choose a smaller local model and update `OLLAMA_MODEL`.

## 6. Tauri

Install Rust using rustup. Then install the Microsoft C++ build tools and WebView2 as required by Tauri's Windows prerequisites.

Verify:

```powershell
rustc --version
cargo --version
```

Then:

```powershell
npm run desktop:dev
```


## Official downloads

- Node.js: https://nodejs.org/en/download/
- Python: https://www.python.org/downloads/windows/
- Ollama: https://ollama.com/download
- Tauri prerequisites: https://tauri.app/start/prerequisites/
- Rust: https://www.rust-lang.org/tools/install
