# SmartGen AI Frontend

React + TypeScript + Vite frontend for the local SmartGen AI FastAPI backend. It preserves the Phase 1 dashboard and connects image generation, PNG preview/download, persisted history, metrics, and benchmarking to `http://127.0.0.1:8000`.

## Run on Windows

Open this folder in PowerShell. If Node.js is installed under `C:\Program Files\nodejs` but is not on `PATH`, add it for this terminal:

```powershell
$env:Path = "C:\Program Files\nodejs;" + $env:Path
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

Open `http://127.0.0.1:5174`. The backend allows this localhost origin. Keep the FastAPI service running on port 8000.

## Build

```powershell
npm run build
```

Generated artwork is template-based procedural SVG rendered locally to PNG; it is not foundation-model text-to-image generation. No paid API or model weights are required.
