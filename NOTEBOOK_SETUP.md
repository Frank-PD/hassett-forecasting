# Jupyter Notebook Setup for VS Code

## 🚀 Quick Start Guide

### 1. Install Required Extensions

Open VS Code and install these extensions:

1. **Jupyter** (`ms-toolsai.jupyter`) - Required
2. **Python** (`ms-python.python`) - Required
3. **Pylance** (`ms-python.vscode-pylance`) - Recommended

**Installation:**
- Press `Cmd+Shift+X` to open Extensions
- Search for "Jupyter" and click Install
- Search for "Python" and click Install

### 2. Set Up Python Environment

```bash
# In VS Code terminal (Cmd+J)
cd /Users/frankgiles/Downloads/hassett-forecasting

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install ipykernel for Jupyter
pip install ipykernel

# Register the kernel
python -m ipykernel install --user --name=hassett-forecasting --display-name="Python (Hassett)"
```

### 3. Select Python Kernel in Notebooks

1. Open a notebook (e.g., `notebooks/00_setup_and_test.ipynb`)
2. Click "Select Kernel" in the top-right corner
3. Choose "Python (Hassett)" or `./venv/bin/python`

### 4. Copy Data Files

```bash
# Copy your database
cp /path/to/hassett.db data/

# Tier mapping should already be there
# If not: cp /path/to/odc_tier_mapping.csv data/
```

---

## 📓 Available Notebooks

### `00_setup_and_test.ipynb` - Environment Verification
**Purpose**: Test that everything is set up correctly

**What it does:**
- ✅ Imports all required packages
- ✅ Connects to hassett.db
- ✅ Loads tier mapping
- ✅ Runs a quick forecasting test
- ✅ Shows environment summary

**Run this first!**

---

### `01_quick_forecast.ipynb` - Generate Forecasts
**Purpose**: Create forecasts using the winning methodology (92-93% accuracy)

**What it does:**
- 📊 Loads historical data from hassett.db
- 🎯 Uses 2022 baseline for MAX, 2024 for EXP
- 📈 Applies YoY trend adjustment
- 🎄 Adds seasonal multiplier (1.27x for peak weeks)
- 📅 Generates day-by-day forecasts
- 📊 Creates visualizations
- 💾 Exports forecast to CSV

**Configurable:**
```python
TARGET_WEEK = 51  # Change this
TARGET_YEAR = 2025  # Change this
```

---

## 🎯 How to Run Notebooks

### Method 1: Run All Cells
1. Open notebook
2. Click "Run All" button at the top
3. Wait for completion (✓ marks appear)

### Method 2: Run Cell-by-Cell
1. Click on a cell
2. Press `Shift+Enter` to run and move to next cell
3. Or press `Cmd+Enter` to run and stay on current cell

### Method 3: Interactive Mode
1. Click on a cell
2. Press `Shift+Enter` to execute
3. Modify code as needed
4. Re-run cells to see updated results

---

## 🔧 Troubleshooting

### "Kernel not found" Error

**Solution:**
```bash
source venv/bin/activate
pip install ipykernel
python -m ipykernel install --user --name=hassett-forecasting
```

Then restart VS Code and select the kernel again.

---

### "No module named 'pandas'" Error

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

Make sure you're using the correct kernel (Python (Hassett)).

---

### "Database not found" Error

**Solution:**
```bash
# Check if database exists
ls data/hassett.db

# If not, copy it
cp /path/to/hassett.db data/
```

Then re-run the notebook.

---

### Plots Not Showing

**Solution:**
Add this at the top of your notebook:
```python
%matplotlib inline
```

Or use:
```python
plt.show()
```

---

## 📊 Notebook Features

### Auto-completion
- Type code and press `Tab` for suggestions
- Works with pandas, numpy, etc.

### Documentation
- Hover over function names to see docstrings
- Press `Shift+Tab` for inline documentation

### Variable Inspector
- Click "Variables" button in notebook toolbar
- See all defined variables and their values

### Output Controls
- Click output area to collapse/expand
- Right-click output → "Clear Output" to reset

---

## 💡 Tips & Tricks

### 1. Restart Kernel
If things get stuck:
- Click "Restart" button in toolbar
- Or: Kernel → Restart in menu

### 2. Clear All Outputs
Clean notebook before committing:
- Click "..." → "Clear All Outputs"

### 3. Export as HTML/PDF
Share results:
- Click "..." → "Export" → Choose format

### 4. Markdown Cells
Document your work:
- Press `Esc` then `M` to convert cell to Markdown
- Press `Esc` then `Y` to convert back to Code

### 5. Cell Magic Commands
Useful commands:
```python
%time code_here  # Time execution
%timeit code_here  # Multiple runs for timing
%load_ext autoreload  # Auto-reload modules
%autoreload 2
```

---

## 🎨 Customization

### Change Plot Style
```python
import matplotlib.pyplot as plt
plt.style.use('seaborn-v0_8-darkgrid')  # Try different styles
```

### Increase Display Rows
```python
pd.set_option('display.max_rows', 200)
```

### Better DataFrame Display
```python
from IPython.display import display
display(df)  # Instead of print(df)
```

---

## 📁 Notebook Organization

```
notebooks/
├── 00_setup_and_test.ipynb      ← START HERE
├── 01_quick_forecast.ipynb      ← Generate forecasts
├── 02_data_exploration.ipynb    ← (Create your own)
├── 03_model_comparison.ipynb    ← (Create your own)
└── 04_validation.ipynb          ← (Create your own)
```

### Naming Convention
- `00-09`: Setup and testing
- `10-19`: Data exploration
- `20-29`: Model development
- `30-39`: Evaluation
- `40-49`: Production

---

## ✅ Checklist

Before running notebooks:

- [ ] Jupyter extension installed
- [ ] Python extension installed
- [ ] Virtual environment created (`venv/`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Kernel registered (`ipykernel install`)
- [ ] Database copied to `data/hassett.db`
- [ ] Tier mapping in `data/odc_tier_mapping.csv`
- [ ] Kernel selected in notebook (top-right)

---

## 🚀 You're Ready!

1. Open `notebooks/00_setup_and_test.ipynb`
2. Select kernel: "Python (Hassett)"
3. Click "Run All"
4. Verify all checks pass ✅

Then proceed to `01_quick_forecast.ipynb` to generate your first forecast!

---

**Need Help?**
- Check `CURSOR_SETUP.md` for AI assistance features
- Review `README.md` for project overview
- See `docs/META_ANALYSIS_100_EXPERIMENTS.md` for methodology

Happy forecasting! 📊🎯
