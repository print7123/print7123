@echo off
chcp 65001
title 서버 상태 확인

echo.
echo ========================================
echo   서버 상태 확인
echo ========================================
echo.

REM 포트 5000 확인
echo [1/3] 포트 5000 사용 확인 중...
netstat -ano | findstr ":5000" >nul 2>&1
if errorlevel 1 (
    echo   ❌ 포트 5000이 사용 중이 아닙니다. 서버가 실행되지 않았습니다.
    echo.
    echo   해결 방법:
    echo   1. 🚀_서버_시작_최종분.bat 파일을 실행하세요
    echo   2. 서버가 시작될 때까지 기다리세요 (약 5-10초)
    echo   3. 브라우저에서 http://localhost:5000 접속
) else (
    echo   ✅ 포트 5000이 사용 중입니다. 서버가 실행 중입니다.
    netstat -ano | findstr ":5000"
)
echo.

REM Python 프로세스 확인
echo [2/3] Python 프로세스 확인 중...
tasklist | findstr "python.exe" >nul 2>&1
if errorlevel 1 (
    echo   ❌ Python 프로세스가 실행 중이 아닙니다.
) else (
    echo   ✅ Python 프로세스가 실행 중입니다:
    tasklist | findstr "python.exe"
)
echo.

REM 파일 확인
echo [3/3] 필수 파일 확인 중...
cd /d "%~dp0"

if exist "app_enhanced_작동중.py" (
    echo   ✅ app_enhanced_작동중.py 존재
) else (
    echo   ❌ app_enhanced_작동중.py 없음
    echo   → 최종_복원_14시작동파일.bat 실행 필요
)

if exist "templates\index.html" (
    echo   ✅ templates\index.html 존재
) else (
    echo   ❌ templates\index.html 없음
)

if exist "requirements.txt" (
    echo   ✅ requirements.txt 존재
) else (
    echo   ❌ requirements.txt 없음
)
echo.

echo ========================================
echo   빠른 해결 방법
echo ========================================
echo.
echo   1. 서버 시작: 🚀_서버_시작_최종분.bat 실행
echo   2. 브라우저에서 접속: http://localhost:5000
echo   3. 문제가 계속되면: 최종_복원_14시작동파일.bat 실행
echo.
pause



