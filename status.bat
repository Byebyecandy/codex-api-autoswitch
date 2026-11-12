@echo off
setlocal
if exist .venv\Scripts\python.exe (set "PY=.venv\Scripts\python.exe") else (set "PY=py -3")
%PY% main.py status
