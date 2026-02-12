@echo off
chcp 65001 >nul
title 온누리인쇄나라 서버 - 즉시 시작 및 자동 실행 설정

echo ========================================
echo 온누리인쇄나라 서버
echo 즉시 시작 + PC 재시작 시 자동 실행 설정
echo ========================================
echo.

REM 현재 디렉토리
set APP_DIR=%~dp0
set SCRIPT_PATH=%APP_DIR%서버_자동_실행_지속구동.bat

echo [1/3] 서버 즉시 시작 중...
echo.

REM 배포 모드 설정
set DEPLOYMENT_MODE=production
set DOMAIN=http://print7123-1.com
set HOST=0.0.0.0
set PORT=5000

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

REM 서버 백그라운드에서 시작
echo 서버를 백그라운드에서 시작합니다...
start "온누리인쇄나라 서버" /min cmd /c "cd /d \"%APP_DIR%\" && set DEPLOYMENT_MODE=%DEPLOYMENT_MODE% && set DOMAIN=%DOMAIN% && set HOST=%HOST% && set PORT=%PORT% && \"%SCRIPT_PATH%\""

timeout /t 3 >nul

echo ✅ 서버가 시작되었습니다!
echo.
echo [2/3] 시작 폴더에 추가 중...
echo.

REM 시작 폴더 경로
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

if not exist "%STARTUP_FOLDER%" mkdir "%STARTUP_FOLDER%"

REM 바로가기 생성
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\온누리인쇄나라_서버_자동실행.lnk'); $Shortcut.TargetPath = '%SCRIPT_PATH%'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Description = '온누리인쇄나라 서버 자동 실행'; $Shortcut.Save()" >nul 2>&1

if exist "%STARTUP_FOLDER%\온누리인쇄나라_서버_자동실행.lnk" (
    echo ✅ 시작 폴더에 추가 완료 (로그인 시 자동 실행)
) else (
    echo ⚠️ 시작 폴더 추가 실패
)
echo.

echo [3/3] 작업 스케줄러 등록 중...
echo.

REM 관리자 권한 확인
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 관리자 권한이 필요합니다.
    echo 작업 스케줄러 등록을 건너뜁니다.
    echo (시작 폴더만으로도 자동 실행됩니다)
) else (
    REM 기존 작업 삭제
    schtasks /delete /tn "온누리인쇄나라_서버_자동실행" /f >nul 2>&1
    
    REM 새 작업 생성
    schtasks /create /tn "온누리인쇄나라_서버_자동실행" /tr "\"%SCRIPT_PATH%\"" /sc onstart /ru "SYSTEM" /rl highest /f >nul 2>&1
    
    if errorlevel 1 (
        echo ⚠️ 작업 스케줄러 등록 실패
    ) else (
        echo ✅ 작업 스케줄러 등록 완료 (Windows 시작 시 자동 실행)
    )
)
echo.

echo ========================================
echo 설정 완료!
echo ========================================
echo.
echo ✅ 서버가 지금 실행 중입니다
echo ✅ PC 재시작 시 자동으로 서버가 시작됩니다
echo.
echo 서버 상태 확인:
echo   - 작업 표시줄에서 "온누리인쇄나라 서버" 창 확인
echo   - 브라우저에서 http://print7123-1.com 접속 확인
echo.
echo 서버를 종료하려면:
echo   - 작업 표시줄의 서버 창을 닫으세요
echo.
echo ========================================
echo.

REM 5초 후 창 닫기
timeout /t 5 >nul

