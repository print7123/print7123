@echo off
chcp 65001
title 서버 시작 - 홈페이지 최종분

echo.
echo ========================================
echo   서버 시작 중...
echo   홈페이지 최종분 26.02.11
echo ========================================
echo.

REM 기존 Python 프로세스 종료
echo [1/5] 기존 서버 종료 중...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 >nul
echo   ✅ 완료
echo.

REM 작업 폴더 확인
echo [2/5] 작업 폴더 확인 중...
cd /d "%~dp0"
echo   ✅ 현재 폴더: %CD%
echo.

REM Python 확인
echo [3/5] Python 확인 중...
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

REM requirements.txt 확인 및 설치
echo [4/5] 필요한 패키지 확인 중...
if exist "requirements.txt" (
    echo   ✅ requirements.txt 파일 발견
    echo   → 필요한 패키지 설치 중... (이미 설치된 패키지는 건너뜁니다)
    pip install -r requirements.txt --quiet --upgrade
    if errorlevel 1 (
        echo   ⚠️  패키지 설치 중 오류가 발생했습니다.
        echo   → 수동으로 설치: pip install -r requirements.txt
    ) else (
        echo   ✅ 패키지 설치 완료
    )
) else (
    echo   ⚠️  requirements.txt 파일이 없습니다.
    echo   → 기본 패키지만 사용합니다.
)
echo.

REM app_enhanced_작동중.py 파일 확인
echo [5/5] 애플리케이션 파일 확인 중...
if not exist "app_enhanced_작동중.py" (
    echo   ❌ app_enhanced_작동중.py 파일을 찾을 수 없습니다.
    echo   → 최종_복원_14시작동파일.bat 파일을 실행하여 파일을 복원하세요.
    pause
    exit /b 1
)
echo   ✅ app_enhanced_작동중.py 파일 확인
echo.

REM 서버 실행
echo ========================================
echo   서버 시작 중...
echo ========================================
echo.
echo   접속 주소: http://localhost:5000
echo   또는: http://127.0.0.1:5000
echo.
echo   관리자 ID: admin
echo   관리자 PW: admin123
echo.
echo   서버를 중지하려면 Ctrl+C를 누르세요
echo ========================================
echo.
echo   서버가 시작되는 동안 잠시 기다려주세요...
echo.

python app_enhanced_작동중.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo   서버 시작 실패
    echo ========================================
    echo.
    echo   오류가 발생했습니다. 위의 오류 메시지를 확인하세요.
    echo.
    echo   일반적인 해결 방법:
    echo   1. 필요한 패키지 설치: pip install -r requirements.txt
    echo   2. 포트 5000이 사용 중인지 확인
    echo   3. Python 버전 확인 (Python 3.7 이상 필요)
    echo   4. 파일 복원: 최종_복원_14시작동파일.bat 실행
    echo.
    pause
)
