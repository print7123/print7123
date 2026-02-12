@echo off
chcp 65001 >nul
echo ========================================
echo 온누리인쇄나라 배포 서버 시작
echo 도메인: http://print7123-1.com
echo ========================================
echo.

REM 배포 모드 설정
set DEPLOYMENT_MODE=production
set DOMAIN=http://print7123-1.com
set HOST=0.0.0.0
set PORT=5000

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM Python 경로 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo Python 3.7 이상을 설치해주세요.
    pause
    exit /b 1
)

echo ✅ Python 확인 완료
echo.

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 필요한 패키지 설치 확인
echo 필요한 패키지 확인 중...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo 필요한 패키지를 설치합니다...
    pip install -r requirements.txt
)

echo.
echo ========================================
echo 서버 시작 중...
echo ========================================
echo.
echo 배포 모드: %DEPLOYMENT_MODE%
echo 도메인: %DOMAIN%
echo 호스트: %HOST%
echo 포트: %PORT%
echo.
echo ⚠️ 프로덕션 환경에서는 WSGI 서버 사용을 권장합니다.
echo    (gunicorn, waitress 등)
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

REM 환경 변수 설정 후 서버 실행
set DEPLOYMENT_MODE=%DEPLOYMENT_MODE%
set DOMAIN=%DOMAIN%
set HOST=%HOST%
set PORT=%PORT%
python app_enhanced_작동중.py

pause

