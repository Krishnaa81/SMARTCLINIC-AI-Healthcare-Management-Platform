@echo off
echo ========================================
echo    SmartClinic AI - Starting Server
echo ========================================
echo.
echo Starting Flask server...
echo.
echo The website will open automatically in your browser.
echo If not, open: http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo ========================================
echo.
cd backend
python app.py
pause
