@echo off
chcp 65001 >nul
echo ========================================
echo 온누리인쇄나라 서버 백그라운드 실행
echo ========================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM 배포 모드 설정
set DEPLOYMENT_MODE=production
set DOMAIN=http://print7123-1.com
set HOST=0.0.0.0
set PORT=5000

REM 백그라운드에서 서버 실행 (새 창에서)
start "온누리인쇄나라 서버" /min cmd /c "서버_자동_실행_지속구동.bat"

echo 서버가 백그라운드에서 실행 중입니다.
echo 작업 표시줄에서 "온누리인쇄나라 서버" 창을 확인하세요.
echo.
echo 서버를 종료하려면 작업 표시줄의 서버 창을 닫으세요.
echo.
pause

