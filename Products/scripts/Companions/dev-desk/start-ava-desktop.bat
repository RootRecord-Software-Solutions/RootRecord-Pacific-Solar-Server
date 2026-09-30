@echo off
cd /d "%~dp0"
if not exist "node_modules\electron\dist\electron.exe" (
  echo Installing Electron binary...
  call npm explore electron -- node install.js
)
start "" "node_modules\electron\dist\electron.exe" .
