@echo off
chcp 65001 >nul
REM Browser Bookmarks Manager Build Script

echo ======================================
echo Browser Bookmarks Manager Build Script
echo ======================================
echo.

REM Python version check
python --version
if %errorlevel% neq 0 (
    echo Error: Python not found!
    pause
    exit /b 1
)

REM PyInstaller check
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [1/2] Building updater.exe...
echo.

REM Build updater.exe
pyinstaller --onefile --console --name "updater" --clean --icon="icon/icon.ico" updater.py

if %errorlevel% neq 0 (
    echo Updater build failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Building portable version...
echo.

REM Build portable version
pyinstaller --onefile --windowed --name "BrowserBookmarks" --clean --icon="icon/icon.ico" --add-data="icon;icon" --add-data="language;language" winBookmarks.py

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Calculating SHA256...
echo.

REM Calculate SHA256
@REM powershell -Command "Get-FileHash -Path 'dist\BrowserBookmarks.exe' -Algorithm SHA256 | Select-Object -ExpandProperty Hash"
@REM powershell -Command "Get-FileHash -Path 'dist\updater.exe' -Algorithm SHA256 | Select-Object -ExpandProperty Hash"

echo.
echo Build complete!
echo.

echo Output files:
echo - dist\BrowserBookmarks.exe (Portable version)
echo - dist\updater.exe (Updater)
echo.

echo ======================================
echo Build process complete!
echo ======================================
pause
