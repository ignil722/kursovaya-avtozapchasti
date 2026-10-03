@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Virtual environment not found: .venv\Scripts\python.exe
  echo Create it in PyCharm: Settings ^> Python Interpreter ^> Add Local Interpreter ^> Virtualenv.
  exit /b 1
)

echo [1/3] Applying database migrations...
".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 exit /b 1

echo [2/3] Preparing demo data...
".venv\Scripts\python.exe" manage.py seed_demo
if errorlevel 1 exit /b 1

echo [3/3] Starting AutoParts Hub at http://127.0.0.1:8000/
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000

endlocal
