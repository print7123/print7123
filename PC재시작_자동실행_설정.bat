@echo off
chcp 65001 >nul
echo ========================================
echo PC 재시작 시 자동 실행 설정
echo 온누리인쇄나라 서버
echo ========================================
echo.
echo 이 스크립트는 PC가 재시작되어도 서버가 자동으로
echo 시작되도록 여러 방법을 설정합니다.
echo.

REM 관리자 권한 확인
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 관리자 권한이 필요합니다.
    echo.
    echo 이 파일을 우클릭하여 "관리자 권한으로 실행"을 선택해주세요.
    pause
    exit /b 1
)

echo ✅ 관리자 권한 확인 완료
echo.

REM 현재 디렉토리
set APP_DIR=%~dp0
set SCRIPT_PATH=%APP_DIR%서버_자동_실행_지속구동.bat

echo ========================================
echo 방법 1: 시작 폴더에 추가
echo ========================================
echo.

REM 시작 폴더 경로
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

echo 시작 폴더에 바로가기 생성 중...
if not exist "%STARTUP_FOLDER%" mkdir "%STARTUP_FOLDER%"

REM 바로가기 생성 (PowerShell 사용)
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\온누리인쇄나라_서버_자동실행.lnk'); $Shortcut.TargetPath = '%SCRIPT_PATH%'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Description = '온누리인쇄나라 서버 자동 실행'; $Shortcut.Save()"

if exist "%STARTUP_FOLDER%\온누리인쇄나라_서버_자동실행.lnk" (
    echo ✅ 시작 폴더에 바로가기 추가 완료
) else (
    echo ⚠️ 시작 폴더 추가 실패 (수동으로 추가해주세요)
)
echo.

echo ========================================
echo 방법 2: 작업 스케줄러 등록
echo ========================================
echo.

REM 기존 작업 삭제
schtasks /delete /tn "온누리인쇄나라_서버_자동실행" /f >nul 2>&1

REM 새 작업 생성 (시작 시 실행)
schtasks /create /tn "온누리인쇄나라_서버_자동실행" /tr "\"%SCRIPT_PATH%\"" /sc onstart /ru "SYSTEM" /rl highest /f

if errorlevel 1 (
    echo ⚠️ 작업 스케줄러 등록 실패
) else (
    echo ✅ 작업 스케줄러 등록 완료
    echo    (Windows 시작 시 자동 실행)
)
echo.

echo ========================================
echo 방법 3: Windows 서비스 등록 (선택사항)
echo ========================================
echo.
set /p install_service="Windows 서비스로도 등록하시겠습니까? (Y/N): "

if /i "%install_service%"=="Y" (
    echo.
    echo Windows 서비스 등록 중...
    call "%APP_DIR%Windows_서비스_등록.bat"
) else (
    echo 서비스 등록을 건너뜁니다.
)
echo.

echo ========================================
echo 설정 완료!
echo ========================================
echo.
echo 다음 방법으로 서버가 자동으로 시작됩니다:
echo.
echo 1. ✅ 시작 폴더: 사용자 로그인 시 자동 실행
echo 2. ✅ 작업 스케줄러: Windows 시작 시 자동 실행
if /i "%install_service%"=="Y" (
    echo 3. ✅ Windows 서비스: Windows 시작 시 자동 실행 (가장 안정적)
)
echo.
echo 서버를 지금 시작하시겠습니까?
set /p start_now="지금 시작 (Y/N): "

if /i "%start_now%"=="Y" (
    echo.
    echo 서버 시작 중...
    start "" "%SCRIPT_PATH%"
    echo.
    echo ✅ 서버가 시작되었습니다!
    timeout /t 2 >nul
)

echo.
echo ========================================
echo 확인 방법:
echo ========================================
echo 1. 시작 폴더 확인:
echo    Win+R → shell:startup
echo.
echo 2. 작업 스케줄러 확인:
echo    Win+R → taskschd.msc
echo    "온누리인쇄나라_서버_자동실행" 작업 확인
echo.
echo 3. 서비스 확인 (서비스 등록한 경우):
echo    Win+R → services.msc
echo    "온누리인쇄나라 웹서버" 서비스 확인
echo.
echo PC를 재시작하면 서버가 자동으로 시작됩니다!
echo.
pause

