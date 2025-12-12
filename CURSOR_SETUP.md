# Cursor Setup Guide for Hassett Forecasting

## ✅ Repository Successfully Created!

**Location**: `/Users/frankgiles/Downloads/hassett-forecasting`

---

## 📦 Recommended Cursor Extensions

### Essential (Install These First)

1. **Python** (`ms-python.python`)
   - Core Python language support
   - IntelliSense, linting, debugging

2. **Pylance** (`ms-python.vscode-pylance`)
   - Fast Python language server
   - Type checking, auto-completion

3. **Black Formatter** (`ms-python.black-formatter`)
   - Code formatting (PEP 8)
   - Auto-format on save

4. **Jupyter** (`ms-toolsai.jupyter`)
   - Jupyter notebook support
   - Interactive data exploration

5. **GitLens** (`eamodio.gitlens`)
   - Enhanced Git capabilities
   - Blame annotations, history

### Data Science Specific

6. **Data Preview** (`randomfractalsInc.vscode-data-preview`)
   - Preview CSV, JSON, Arrow files
   - Essential for data validation

7. **Rainbow CSV** (`mechatroner.rainbow-csv`)
   - Colorize CSV columns
   - CSV query support

8. **SQLite Viewer** (`qwtel.sqlite-viewer`)
   - View hassett.db directly
   - Run SQL queries in Cursor

### Code Quality

9. **Flake8** (`ms-python.flake8`)
   - Python linting
   - Catch errors early

10. **MyPy** (`ms-python.mypy-type-checker`)
    - Static type checking
    - Find type errors

11. **Code Spell Checker** (`streetsidesoftware.code-spell-checker`)
    - Catch typos in code/comments
    - Custom dictionary support

### Documentation

12. **Markdown All in One** (`yzhang.markdown-all-in-one`)
    - Markdown preview, shortcuts
    - Table of contents generation

13. **autoDocstring** (`njpwerner.autodocstring`)
    - Generate Python docstrings
    - Google/NumPy/Sphinx formats

---

## 🚀 Quick Install Commands

Open Cursor Command Palette (Cmd+Shift+P) and run:

```
ext install ms-python.python
ext install ms-python.vscode-pylance
ext install ms-python.black-formatter
ext install ms-toolsai.jupyter
ext install eamodio.gitlens
ext install randomfractalsInc.vscode-data-preview
ext install mechatroner.rainbow-csv
ext install qwtel.sqlite-viewer
ext install ms-python.flake8
ext install streetsidesoftware.code-spell-checker
ext install yzhang.markdown-all-in-one
ext install njpwerner.autodocstring
```

Or install them manually:
1. Open Extensions (Cmd+Shift+X)
2. Search for each extension
3. Click "Install"

---

## ⚙️ Cursor Settings (Already Configured)

The following settings are pre-configured in `.vscode/settings.json`:

✅ **Python Interpreter**: Uses `venv/bin/python`
✅ **Auto-formatting**: Black on save (100 char line length)
✅ **Linting**: Flake8 enabled
✅ **Testing**: Pytest configured
✅ **Auto-save**: 1-second delay
✅ **Git**: Ignore limits for large repos

---

## 🔧 Initial Setup Steps

### 1. Create Virtual Environment

```bash
cd /Users/frankgiles/Downloads/hassett-forecasting
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Copy Data Files

```bash
# Copy your database
cp /path/to/hassett.db data/

# Copy tier mapping (already done)
# cp /path/to/odc_tier_mapping.csv data/
```

### 4. Select Python Interpreter in Cursor

1. Press `Cmd+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose `./venv/bin/python`

### 5. Verify Installation

```bash
# In Cursor terminal
python -c "import pandas, numpy, sklearn; print('All packages installed!')"
```

---

## 🎯 Cursor AI Features to Use

### 1. **Cmd+K** - Inline AI Edit
- Select code, press Cmd+K
- Ask AI to refactor, add docstrings, etc.
- Example: "Add type hints to this function"

### 2. **Cmd+L** - Chat with AI
- Ask questions about the codebase
- Get code explanations
- Example: "How does the YoY trend calculation work?"

### 3. **Tab** - Auto-complete
- AI-powered code completion
- Accepts suggestions with Tab

### 4. **Cmd+I** - Composer
- Multi-file edits
- Complex refactoring
- Example: "Create unit tests for all functions in src/"

---

## 📝 Cursor Rules (Already Set)

The `.cursorrules` file contains:
- Project-specific context (forecasting system, 92-93% accuracy)
- Coding standards (PEP 8, type hints, docstrings)
- Architecture patterns (dependency injection, factory pattern)
- Forecasting best practices (2022 for MAX, 2024 for EXP)
- Testing requirements (>80% coverage)

**The AI will automatically follow these rules!**

---

## 🗂️ Project Structure Created

```
hassett-forecasting/
├── .cursorrules          ← AI behavior rules
├── .gitignore           ← Git ignore patterns
├── .vscode/
│   ├── extensions.json  ← Recommended extensions
│   └── settings.json    ← Cursor settings
├── README.md            ← Project documentation
├── requirements.txt     ← Python dependencies
├── setup.py            ← Package setup
│
├── src/                ← Source code (empty, ready for you)
├── data/               ← Data files (gitignored)
├── models/             ← Trained models (gitignored)
├── notebooks/          ← Jupyter notebooks
├── docs/               ← Documentation
│   ├── META_ANALYSIS_100_EXPERIMENTS.md
│   ├── EXECUTIVE_SUMMARY_100_EXPERIMENTS.txt
│   └── FORECASTING_PACKAGES_USED.md
└── tests/              ← Unit tests
```

---

## ✨ Next Steps

### Immediate Actions:

1. ✅ **Repository created** - Done!
2. ✅ **Cursor opened** - Should be open now!
3. ⏳ **Install extensions** - Follow list above
4. ⏳ **Create virtual environment** - See commands above
5. ⏳ **Install dependencies** - `pip install -r requirements.txt`

### Development:

1. **Copy your data files** to `data/` folder
2. **Start coding** in `src/` folder
3. **Create notebooks** in `notebooks/` for exploration
4. **Write tests** in `tests/` folder
5. **Use Cmd+K and Cmd+L** to get AI assistance

### Git Workflow:

```bash
# Already committed initial structure
git log  # See initial commit

# When you make changes:
git add .
git commit -m "feat: Add forecasting engine"
git push  # (after setting up remote)
```

---

## 🐛 Troubleshooting

### Python Interpreter Not Found
1. Press `Cmd+Shift+P`
2. "Python: Select Interpreter"
3. Choose `./venv/bin/python`

### Extensions Not Working
1. Restart Cursor
2. Check extension is enabled (Extensions panel)
3. Check Python interpreter is selected

### Import Errors
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall packages
pip install -r requirements.txt
```

### Linting Errors
```bash
# Install dev dependencies
pip install black flake8 mypy pytest
```

---

## 📚 Useful Cursor Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Inline AI edit |
| `Cmd+L` | Chat with AI |
| `Cmd+I` | Composer (multi-file edit) |
| `Cmd+Shift+P` | Command palette |
| `Cmd+P` | Quick file open |
| `Cmd+Shift+F` | Search in files |
| `Cmd+B` | Toggle sidebar |
| `Cmd+J` | Toggle terminal |
| `Cmd+Shift+E` | Explorer view |
| `Cmd+Shift+X` | Extensions view |

---

## 🎓 Learning Resources

- **Cursor Docs**: https://cursor.sh/docs
- **Python Best Practices**: PEP 8
- **Forecasting Methodology**: See `docs/META_ANALYSIS_100_EXPERIMENTS.md`
- **Pandas Time Series**: https://pandas.pydata.org/docs/user_guide/timeseries.html
- **scikit-learn**: https://scikit-learn.org/stable/

---

**You're all set! Start coding with AI assistance!** 🚀

Press `Cmd+L` in Cursor to chat with AI about the codebase.
