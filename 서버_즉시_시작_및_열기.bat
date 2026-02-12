@echo off
chcp 65001
title 서버 즉시 시작 및 브라우저 열기

echo.
echo ========================================
echo   서버 즉시 시작 및 브라우저 열기
echo ========================================
echo.

cd /d "%~dp0"

REM 기존 Python 프로세스 종료
echo [1/5] 기존 서버 종료 중...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 >nul
echo   ✅ 완료
echo.

REM Python 확인
echo [2/5] Python 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ❌ Python이 설치되어 있지 않습니다.
    echo   → Python을 설치하세요: https://www.python.org/
    pause
    exit /b 1
)
python --version
echo   ✅ Python 확인 완료
echo.

REM 파일 확인
echo [3/5] 필수 파일 확인 중...
if not exist "app_enhanced_작동중.py" (
    echo   ❌ app_enhanced_작동중.py 파일이 없습니다.
    echo   → 최종_복원_14시작동파일.bat 파일을 먼저 실행하세요.
    pause
    exit /b 1
)
echo   ✅ app_enhanced_작동중.py 확인
echo.

REM 서버 백그라운드 시작
echo [4/5] 서버 시작 중...
echo   → 서버가 백그라운드에서 시작됩니다...
start /B python app_enhanced_작동중.py
echo   ✅ 서버 시작 명령 실행
echo.

REM 서버 시작 대기
echo [5/5] 서버 시작 대기 중...
echo   → 서버가 시작될 때까지 최대 15초 대기...
timeout /t 3 >nul

REM 서버 상태 확인 (최대 5번 시도)
set "SERVER_STARTED=0"
for /L %%i in (1,1,5) do (
    netstat -ano | findstr ":5000" >nul 2>&1
    if not errorlevel 1 (
        set "SERVER_STARTED=1"
        goto :server_ready
    )
    timeout /t 2 >nul
    echo   → 서버 시작 대기 중... (%%i/5)
)

:server_ready
if "%SERVER_STARTED%"=="1" (
    echo   ✅ 서버가 시작되었습니다!
    echo.
    echo ========================================
    echo   브라우저 열기
    echo ========================================
    echo.
    timeout /t 1 >nul
    start http://localhost:5000
    echo   ✅ 브라우저가 열렸습니다.
    echo.
    echo   접속 주소: http://localhost:5000
    echo   관리자 ID: admin
    echo   관리자 PW: admin123
    echo.
    echo   서버를 중지하려면 작업 관리자에서 python.exe를 종료하세요.
) else (
    echo   ⚠️  서버 시작에 시간이 걸리고 있습니다.
    echo   → 브라우저를 수동으로 열어주세요: http://localhost:5000
    echo   → 또는 잠시 후 다시 시도하세요.
    timeout /t 2 >nul
    start http://localhost:5000
)
echo.
echo ========================================
pause



