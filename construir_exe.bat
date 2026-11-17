@echo off
rem Crea dist\NebulaLauncher.exe (un solo archivo, sin consola, con el icono de Nebula).
rem Dentro van la interfaz (ui), config.json y proyectos.ejemplo.json. Los datos del jugador siguen en %%APPDATA%%\.nebula
cd /d "%~dp0"
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name NebulaLauncher ^
  --icon recursos\nebula.ico ^
  --add-data "ui;ui" ^
  --add-data "config.json;." ^
  --add-data "proyectos.ejemplo.json;." ^
  --collect-data minecraft_launcher_lib ^
  --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module PySide2 --exclude-module PySide6 ^
  --exclude-module qtpy --exclude-module tkinter --exclude-module numpy --exclude-module PIL ^
  --exclude-module webview.platforms.qt --exclude-module webview.platforms.gtk ^
  --exclude-module webview.platforms.cef --exclude-module webview.platforms.cocoa ^
  --exclude-module webview.platforms.android ^
  nebula.py
