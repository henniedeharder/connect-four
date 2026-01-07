# Connect Four (Beautiful Pygame Edition)

A polished, animated Connect Four built with Python and Pygame.

## Features
- 1 Player vs Computer (Easy/Medium/Hard with minimax + alpha-beta)
- 2 Players local
- Smooth drop animations
- Modern look: gradient background, glossy tokens, cut-out board
- Resizable window with responsive layout

## Quick Start

### Prerequisites
- Python 3.9 or newer recommended (not 3.13, might give installation issues)

### Create a virtual environment

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Run the game
```bash
python connect_four.py
```

## Controls
- Mouse: click at a column to drop
- R: restart the current match
- ESC: return to Main Menu

## Modes
- 2 Players (Local)
- 1 Player vs AI (Easy / Medium / Hard)

## Project Structure
```
.
├── connect_four.py        # Game code (Pygame UI + AI)
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore rules
├── README.md              # This file
└── scripts/
    ├── setup_venv.sh      # Optional helper (macOS/Linux)
    └── setup_venv.ps1     # Optional helper (Windows PowerShell)
```

## Optional: one-liner setup
macOS/Linux:
```bash
bash scripts/setup_venv.sh
```
Windows (PowerShell):
```powershell
./scripts/setup_venv.ps1
```

## Troubleshooting
- If the window does not appear on macOS, ensure you are using a framework-enabled Python (default from python.org works) and that the app has permission to open windows.
- Update your GPU drivers if you experience rendering issues.
