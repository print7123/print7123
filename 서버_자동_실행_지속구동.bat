@echo off
chcp 65001 >nul
title 온누리인쇄나라 서버 - 자동 재시작 모드

REM 서버가 종료되면 자동으로 재시작하는 스크립트
REM 무한 루프로 서버를 계속 실행

:START
echo ========================================
echo 온누리인쇄나라 서버 자동 실행
echo 도메인: http://print7123-1.com
echo ========================================
echo.
echo [%date% %time%] 서버 시작 중...
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
    echo [%date% %time%] ❌ Python이 설치되어 있지 않습니다.
    echo Python 3.7 이상을 설치해주세요.
    timeout /t 10
    goto START
)

REM 필요한 패키지 확인
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [%date% %time%] 필요한 패키지를 설치합니다...
    pip install -r requirements.txt
)

REM 환경 변수 설정
set DEPLOYMENT_MODE=%DEPLOYMENT_MODE%
set DOMAIN=%DOMAIN%
set HOST=%HOST%
set PORT=%PORT%

REM 서버 실행
echo [%date% %time%] 서버 실행 중...
echo.
python app_enhanced_작동중.py

REM 서버가 종료된 경우 (정상 종료 또는 오류)
echo.
echo ========================================
echo [%date% %time%] 서버가 종료되었습니다.
echo 5초 후 자동으로 재시작합니다...
echo 서버를 완전히 종료하려면 이 창을 닫으세요.
echo ========================================
echo.

REM 5초 대기 후 재시작
timeout /t 5 /nobreak >nul

REM 재시작
goto START

