@echo off
rem Starts CV Builder at http://localhost:8000 and opens it in the browser.
rem Stop it with Ctrl+C or by closing this window.
rem
rem The script re-runs itself with input from NUL, so Ctrl+C does not
rem leave you at a "Terminate batch job (Y/N)?" question afterwards.
if not "%~1"=="--run" (
  call "%~f0" --run <NUL
  if errorlevel 9009 pause
  exit /b
)
cd /d "%~dp0"
python serve.py
if errorlevel 9009 echo Python was not found. Install it from https://www.python.org and tick "Add python.exe to PATH".
exit /b %errorlevel%
