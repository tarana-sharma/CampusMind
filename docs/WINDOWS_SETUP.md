# CampusMind: Windows 11 Setup Guide

## Prerequisites

- Python 3.10 or newer, with Python Launcher (`py`) or Python on PATH
- Node.js 20+ with npm (`node -v`, `npm -v`)
- VS Code is optional but recommended
- Active internet connection **only for first dependency installation**

## Install

1. Right-click the downloaded ZIP and choose **Extract All**.
2. Open the extracted `CampusMind` folder. You should see `backend`, `frontend`, `data`, and `scripts`.
3. Open `scripts`, double-click `01_SETUP_WINDOWS.bat`.
4. Leave the terminal open until it prints **SETUP COMPLETE**. A "Press any key" prompt is normal.
5. If it displays **SETUP FAILED**, read the error above it or send a screenshot. The installer checks failures rather than silently continuing.

The script creates `.venv/`, installs `backend/requirements.txt`, and runs `npm install` in `frontend/`.

## Start the project (every time)

**Simplest: double-click `scripts/05_START_CAMPUSMIND.bat`.**

It opens two windows for backend and frontend, then the dashboard in your browser. Keep both windows open. To stop the services press `Ctrl+C` once in each window and close the terminals.

Or use the two launchers:

- `02_START_BACKEND.bat` (FastAPI on http://127.0.0.1:8000)
- `03_START_FRONTEND.bat` (Vite on http://127.0.0.1:5173)

The backend must be running for scenario loads, edits, scheduling and algorithm comparisons to work.

## Check setup

- Backend API: http://127.0.0.1:8000/docs
- Backend status: http://127.0.0.1:8000/api/health
- CampusMind dashboard: http://127.0.0.1:5173
- Unit tests: `04_RUN_TESTS.bat`

## Troubleshooting

| Problem | Fix |
|---|---|
| `python is not recognized` | Install Python 3.10+ or enable PATH, reopen terminals |
| `node/npm is not recognized` | Install Node.js LTS, reopen VS Code |
| npm installation blocked by firewall | Connect to the internet and retry setup; use configured registry/proxy |
| Port 8000 is already in use | Stop another backend (e.g., RescueNet), then restart CampusMind |
| Port 5173 is already in use | Stop another React/Vite project (e.g., RescueNet), then restart CampusMind |
| Dashboard cannot connect to backend | Start `02_START_BACKEND.bat` and check http://127.0.0.1:8000/api/health |
| Python venv activation blocked by PowerShell | Use provided `.bat` files; they call `.venv\Scripts\python.exe` directly |
| Script says `Press any key` then closes | Normal; it finished. Verify **SETUP COMPLETE** was printed first |
| Browser shows a blank page | Inspect browser DevTools Console and confirm `npm install` succeeded |
| Exact coloring refuses >13 courses | Use DSATUR or reduce exam count; exact optimization is exponentially expensive |
| Room allocation says infeasible | Increase room capacities, add compatible facilities or change the exam model |

## Safety and data

`.bat` scripts are plain text. You can right-click -> Edit to inspect them. Windows may warn "Unknown publisher" because they are unsigned. Only run files from sources you trust. The seeded data and all algorithm run history are stored locally in `data/campusmind.db`. No cloud account is needed.

## Moving your project

You may move the entire extracted folder anywhere. Script paths are relative; do **not** move individual `.bat` files out of `scripts/`. If you move an existing Python virtual environment across drive locations, reinstall via `01_SETUP_WINDOWS.bat`.
