# 📦 STREAMLIT INSTALLATION GUIDE FOR UBUNTU

## ⚡ QUICK ANSWER

**Terminal to open:** Any terminal (Terminal, Konsole, etc.)  
**Command to run:** `pip install streamlit`

---

## 🖥️ STEP-BY-STEP INSTALLATION

### **Step 1: Open a Terminal**

#### **Option A: Using GUI**
1. Click the **Terminal icon** in your taskbar (usually bottom left)
2. OR press **Ctrl + Alt + T** (keyboard shortcut)

#### **Option B: Using Menu**
1. Click Applications menu
2. Search for "Terminal"
3. Click to open

**You should see:**
```
username@computer:~$
```

---

### **Step 2: Check Python Version**

```bash
python3 --version
```

**Expected output:**
```
Python 3.8+ (or higher)
```

**If not installed:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

---

### **Step 3: Install Streamlit**

In the terminal, type:

```bash
pip install streamlit
```

**What you'll see:**
```
Collecting streamlit
Downloading streamlit-1.xx.x-...
Installing collected packages: ...
Successfully installed streamlit-1.xx.x
```

---

### **Step 4: Verify Installation**

```bash
streamlit --version
```

**Expected output:**
```
Streamlit, version 1.xx.x
```

✅ **Installation successful!**

---

## 🚀 FULL INSTALLATION PROCESS (Copy-Paste)

### **In Terminal, Run These Commands:**

```bash
# Step 1: Update package manager
sudo apt update

# Step 2: Install Python if not already installed
sudo apt install python3 python3-pip

# Step 3: Install Streamlit
pip install streamlit

# Step 4: Verify installation
streamlit --version
```

---

## 🎯 THEN RUN THE UI

Once Streamlit is installed, in the same terminal:

```bash
# Navigate to project directory
cd /home/ubuntu/Desktop/demo

# Run the Streamlit app
streamlit run app.py
```

**Browser will open automatically at:**
```
http://localhost:8501
```

---

## 📋 COMPLETE WORKFLOW

### **Terminal Commands (In Order):**

```bash
# 1. Install Streamlit (one-time only)
pip install streamlit

# 2. Navigate to project
cd /home/ubuntu/Desktop/demo

# 3. Check what files are there
ls -lh app.py

# 4. Run the UI
streamlit run app.py
```

---

## ✅ TROUBLESHOOTING

### **Problem: Command not found (streamlit)**

**Solution:**
```bash
# Try with Python module
python3 -m streamlit run app.py

# OR check if pip installed it correctly
pip show streamlit

# OR reinstall
pip install --upgrade streamlit
```

### **Problem: "Permission denied"**

**Solution:**
```bash
# Use sudo
sudo pip install streamlit

# OR use user-level install (recommended)
pip install --user streamlit
```

### **Problem: Port 8501 already in use**

**Solution:**
```bash
# Use different port
streamlit run app.py --server.port 8502
```

### **Problem: ModuleNotFoundError**

**Solution:**
```bash
# Install missing dependencies
pip install streamlit pandas numpy plotly
```

---

## 🔧 ALTERNATIVE: INSTALL WITH REQUIREMENTS

If the project has `requirements.txt`:

```bash
# Navigate to project
cd /home/ubuntu/Desktop/demo

# Install all dependencies at once
pip install -r requirements.txt

# Then run
streamlit run app.py
```

---

## 📊 WHAT EACH COMMAND DOES

| Command | What it does |
|---------|------------|
| `pip install streamlit` | Installs Streamlit package |
| `streamlit --version` | Shows installed version |
| `streamlit run app.py` | Starts the UI |
| `python3 -m streamlit run app.py` | Alternative way to run |

---

## 🎮 AFTER INSTALLATION

### **To Start the UI Every Time:**

```bash
# Open terminal (Ctrl+Alt+T)
cd /home/ubuntu/Desktop/demo
streamlit run app.py
```

**That's it!** Browser opens automatically.

---

## 📱 WHAT YOU'LL SEE

### **In Terminal:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501

  Press CTRL+C to stop the server
```

### **In Browser:**
- Streamlit logo
- "Submit Application" form
- Analytics dashboard
- Application history

---

## ✨ OPTIONAL: Create a Shortcut Script

### **Create `start_ui.sh`:**

```bash
#!/bin/bash
cd /home/ubuntu/Desktop/demo
streamlit run app.py
```

### **Make it executable:**
```bash
chmod +x start_ui.sh
```

### **Run anytime:**
```bash
./start_ui.sh
```

---

## 🎯 FINAL CHECKLIST

- [ ] Open terminal (Ctrl+Alt+T)
- [ ] Run: `pip install streamlit`
- [ ] Wait for installation to complete
- [ ] Run: `cd /home/ubuntu/Desktop/demo`
- [ ] Run: `streamlit run app.py`
- [ ] Browser opens at http://localhost:8501
- [ ] Fill form with test data
- [ ] Click "Submit Application"
- [ ] See decision results

---

## 📞 QUICK REFERENCE

```bash
# One-liner to do everything:
pip install streamlit && streamlit run app.py
```

---

**That's all you need!** 🚀

