@echo off
setlocal
py -3 -m venv .venv
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%
echo Installed. Run doctor.bat to inspect your environment.
pause
