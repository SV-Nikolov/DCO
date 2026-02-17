# Troubleshooting Guide for DCO Executable

## Problem: "ModuleNotFoundError: No module named 'PySide6'"

The PyInstaller build is having trouble bundling PySide6 with Python 3.13. This is a known compatibility issue with newer Python versions and Qt bindings.

## Solutions (Choose One)

### **Solution 1: Run Directly with Python (RECOMMENDED for testing)**

This is the easiest way to test the application right now.

1. **Make sure dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run using the batch file:**
   ```bash
   run_dco.bat
   ```
   
   OR run directly:
   ```bash
   python app.py
   ```

**Pros:** Works immediately, no compilation needed  
**Cons:** Requires Python to be installed

---

### **Solution 2: Use Python 3.11 for Building**

PyInstaller works better with Python 3.11 than 3.13.

1. **Install Python 3.11** from [python.org](https://www.python.org/downloads/)

2. **Create a virtual environment with Python 3.11:**
   ```bash
   py -3.11 -m venv venv311
   venv311\Scripts\activate
   pip install -r requirements.txt
   python -m PyInstaller --noconfirm --clean DailyChessOffline.spec
   ```

3. **The executable will be in:** `dist\DailyChessOffline\`

---

### **Solution 3: Create Portable Distribution**

Instead of a single .exe, create a portable folder with Python included.

1. **Download Python embeddable package:**
   - Go to [python.org](https://www.python.org/downloads/windows/)
   - Download "Windows embeddable package (64-bit)" for Python 3.11
   
2. **Extract to a folder:** `DCO_Portable\python`

3. **Copy your app files:**
   ```
   DCO_Portable\
   ├── python\          (embeddable Python)
   ├── app.py
   ├── dco\
   ├── requirements.txt
   └── launch.bat
   ```

4. **Create launch.bat:**
   ```batch
   @echo off
   cd /d "%~dp0"
   python\python.exe -m pip install -r requirements.txt --target python\Lib\site-packages
   python\python.exe app.py
   ```

---

### **Solution 4: Manual PyInstaller Debug**

Try building with more explicit settings:

```bash
python -m PyInstaller --clean --onedir --windowed ^
  --collect-all PySide6 ^
  --collect-all shiboken6 ^
  --copy-metadata PySide6 ^
  --recursive-copy-metadata PySide6 ^
  --add-data "dco;dco" ^
  --hidden-import=PySide6.QtCore ^
  --hidden-import=PySide6.QtGui ^
  --hidden-import=PySide6.QtWidgets ^
  --hidden-import=shiboken6 ^
  --name=DailyChessOffline ^
  app.py
```

---

## Current Workaround (What Works Now)

**Use the batch file launcher:**

1. Double-click `run_dco.bat` in the DCO folder
2. It will check for dependencies and install them if needed
3. It will launch the application

This requires Python installed, but it's the most reliable way to test the application right now.

---

## Why This Happens

PyInstaller has difficulty with:
- Python 3.13 (too new, limited PyInstaller support)
- PySide6's complex binary dependencies
- Qt plugins and platform-specific files

The issue is not with your code—it's a packaging limitation.

---

## For Distribution

If you need to distribute to users without Python:

1. **Use Python 3.11** instead of 3.13 for building
2. **Or use the Portable Python approach** (Solution 3)
3. **Or provide an installer** that includes Python + dependencies

---

## Testing Right Now

**Easiest method:**

```bash
# In the DCO folder:
python app.py
```

That's it! The application will launch with the GUI.
