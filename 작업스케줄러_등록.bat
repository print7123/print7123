@echo off
chcp 65001 >nul
echo ========================================
echo 온누리인쇄나라 작업 스케줄러 등록
echo ========================================
echo.
echo 이 스크립트는 Windows 작업 스케줄러를 사용하여
echo 서버를 자동으로 시작하고 지속적으로 실행합니다.
echo.

REM 현재 디렉토리
set APP_DIR=%~dp0
set SCRIPT_PATH=%APP_DIR%서버_자동_실행_지속구동.bat

echo 작업 정보:
echo   작업 이름: 온누리인쇄나라_서버_자동실행
echo   스크립트: %SCRIPT_PATH%
echo.

set /p confirm="작업 스케줄러에 등록하시겠습니까? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 작업 스케줄러 등록 중...

REM 기존 작업 삭제 (있는 경우)
schtasks /delete /tn "온누리인쇄나라_서버_자동실행" /f >nul 2>&1

REM 새 작업 생성
schtasks /create /tn "온누리인쇄나라_서버_자동실행" /tr "\"%SCRIPT_PATH%\"" /sc onstart /ru "SYSTEM" /rl highest /f

if errorlevel 1 (
    echo ❌ 작업 등록 실패
    echo 관리자 권한으로 실행해주세요.
    pause
    exit /b 1
)

echo ✅ 작업이 성공적으로 등록되었습니다!
echo.

REM 작업 즉시 실행
echo 작업 즉시 실행 중...
schtasks /run /tn "온누리인쇄나라_서버_자동실행"

echo.
echo ========================================
echo 작업 스케줄러 관리 명령어:
echo ========================================
echo 작업 실행:   schtasks /run /tn "온누리인쇄나라_서버_자동실행"
echo 작업 중지:   schtasks /end /tn "온누리인쇄나라_서버_자동실행"
echo 작업 삭제:   schtasks /delete /tn "온누리인쇄나라_서버_자동실행" /f
echo 작업 확인:   schtasks /query /tn "온누리인쇄나라_서버_자동실행"
echo.
echo 작업은 Windows 시작 시 자동으로 실행됩니다.
echo.
pause

