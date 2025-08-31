# PyQt5 Counter App

A desktop application built with **Python + PyQt5**, designed to manage multiple counters with countdown progress bars, hotkeys, and a system tray menu.

## ✨ Features
- 🖱️ **Interactive Counter**: Click "交互" button to increase count
- ⏳ **Reverse Progress Bar**: Countdown bar with color transitions (green → yellow → red)
- 📝 **Editable Goals**: Double-click the label to modify current (N) / target (A)
- 🔒 **Lock/Unlock**: Press `Ctrl+L` to toggle lock (prevent window movement)
- 📦 **Multiple Counters**: Create 1–6 counters at startup or add more dynamically
- 🖼️ **System Tray Support**: Hide to tray on close, right-click to show/quit
- 🎛 **Global Shortcuts**:  
  - `Alt+P` → Show/Hide all counter windows  
  - `Ctrl+L` → Lock/unlock window movement  
- 📐 **Resizable**: Custom width per counter window

## 🚀 Usage
1. Install dependencies:
   ```bash
   pip install pyqt5


Run the app:
python counter_app.py
