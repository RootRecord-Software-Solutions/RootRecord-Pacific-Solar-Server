@echo off
cd /d "%~dp0"
if exist "dist\AvaIvy-0.1.1-win\Ava Ivy.exe" (start "" "dist\AvaIvy-0.1.1-win\Ava Ivy.exe" & exit /b 0)
if exist "dist\win-unpacked\Ava Ivy.exe" (start "" "dist\win-unpacked\Ava Ivy.exe" & exit /b 0)
if exist "dist\AvaIvy-0.1.0-win\Ava Ivy.exe" (start "" "dist\AvaIvy-0.1.0-win\Ava Ivy.exe" & exit /b 0)
npm start
