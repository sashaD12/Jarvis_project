@echo off
cd /d "%~dp0"

if not exist "frontend\node_modules\" (
  echo Installing frontend dependencies...
  pushd frontend
  call npm install
  if errorlevel 1 (
    echo npm install failed.
    pause
    exit /b 1
  )
  popd
)

if not exist "frontend\dist\index.html" (
  echo Building R.I.A.T. desktop UI...
  pushd frontend
  call npm run build
  if errorlevel 1 (
    echo npm run build failed.
    pause
    exit /b 1
  )
  popd
)

echo Starting R.I.A.T. desktop app...
py -3.13 Start_Jarvis_Program.py
if errorlevel 1 (
  echo.
  echo Program exited with an error.
  pause
)
