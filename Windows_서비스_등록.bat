@echo off
chcp 65001 >nul

REM 관리자 권한 확인
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 관리자 권한이 필요합니다.
    echo.
    echo 이 파일을 우클릭하여 "관리자 권한으로 실행"을 선택해주세요.
    pause
    exit /b 1
)

echo ========================================
echo 온누리인쇄나라 Windows 서비스 등록
echo ========================================
echo.
echo 이 스크립트는 NSSM을 사용하여 서버를 Windows 서비스로 등록합니다.
echo PC가 재시작되어도 자동으로 서버가 시작됩니다.
echo.

REM NSSM 다운로드 및 설치 확인
set NSSM_URL=https://nssm.cc/release/nssm-2.24.zip
set NSSM_DIR=%~dp0nssm

if not exist "%NSSM_DIR%" (
    echo NSSM이 설치되어 있지 않습니다.
    echo.
    echo 옵션 1: 자동 다운로드 (권장)
    echo 옵션 2: 수동 다운로드
    echo.
    set /p choice="선택 (1 또는 2): "
    
    if "!choice!"=="1" (
        echo NSSM 다운로드 중...
        mkdir "%NSSM_DIR%" 2>nul
        powershell -Command "Invoke-WebRequest -Uri '%NSSM_URL%' -OutFile '%NSSM_DIR%\nssm.zip'"
        powershell -Command "Expand-Archive -Path '%NSSM_DIR%\nssm.zip' -DestinationPath '%NSSM_DIR%' -Force"
        echo NSSM 다운로드 완료.
    ) else (
        echo.
        echo 수동 다운로드 방법:
        echo 1. https://nssm.cc/download 에서 NSSM 다운로드
        echo 2. 압축 해제 후 win64 폴더의 nssm.exe를 이 폴더에 복사
        echo 3. 이 스크립트를 다시 실행하세요.
        pause
        exit /b 1
    )
)

REM NSSM 경로 찾기
set NSSM_EXE=
if exist "%NSSM_DIR%\win64\nssm.exe" set NSSM_EXE=%NSSM_DIR%\win64\nssm.exe
if exist "%NSSM_DIR%\nssm.exe" set NSSM_EXE=%NSSM_DIR%\nssm.exe
if exist "%~dp0nssm.exe" set NSSM_EXE=%~dp0nssm.exe

if "%NSSM_EXE%"=="" (
    echo ❌ NSSM을 찾을 수 없습니다.
    echo NSSM을 수동으로 설치해주세요.
    pause
    exit /b 1
)

echo ✅ NSSM 발견: %NSSM_EXE%
echo.

REM Python 경로 찾기
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ Python을 찾을 수 없습니다.
    pause
    exit /b 1
)

for /f "delims=" %%i in ('where python') do set PYTHON_EXE=%%i
echo ✅ Python 발견: %PYTHON_EXE%
echo.

REM 현재 디렉토리
set APP_DIR=%~dp0
set APP_SCRIPT=%APP_DIR%app_enhanced_작동중.py

echo 서비스 정보:
echo   서비스 이름: PrintShopService
echo   표시 이름: 온누리인쇄나라 웹서버
echo   설명: 온누리인쇄나라 홈페이지 서버 (http://print7123-1.com)
echo   실행 파일: %PYTHON_EXE%
echo   인수: %APP_SCRIPT%
echo   작업 디렉토리: %APP_DIR%
echo.

set /p confirm="서비스를 등록하시겠습니까? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 서비스 등록 중...

REM 기존 서비스 제거 (있는 경우)
"%NSSM_EXE%" remove PrintShopService confirm 2>nul

REM 서비스 등록
"%NSSM_EXE%" install PrintShopService "%PYTHON_EXE%" "%APP_SCRIPT%"

if errorlevel 1 (
    echo ❌ 서비스 등록 실패
    pause
    exit /b 1
)

REM 서비스 설정
echo 서비스 설정 중...
"%NSSM_EXE%" set PrintShopService AppDirectory "%APP_DIR%"
"%NSSM_EXE%" set PrintShopService DisplayName "온누리인쇄나라 웹서버"
"%NSSM_EXE%" set PrintShopService Description "온누리인쇄나라 홈페이지 서버 (http://print7123-1.com)"
"%NSSM_EXE%" set PrintShopService Start SERVICE_AUTO_START
"%NSSM_EXE%" set PrintShopService AppEnvironmentExtra "DEPLOYMENT_MODE=production" "DOMAIN=http://print7123-1.com" "HOST=0.0.0.0" "PORT=5000"

REM 서비스 시작
echo.
echo 서비스 시작 중...
net start PrintShopService

if errorlevel 1 (
    echo ⚠️ 서비스 시작 실패 (이미 실행 중일 수 있습니다)
) else (
    echo ✅ 서비스가 성공적으로 시작되었습니다!
)

echo.
echo ========================================
echo 서비스 관리 명령어:
echo ========================================
echo 서비스 시작:   net start PrintShopService
echo 서비스 중지:   net stop PrintShopService
echo 서비스 제거:   "%NSSM_EXE%" remove PrintShopService confirm
echo 서비스 상태:   sc query PrintShopService
echo.
echo 서비스는 Windows 시작 시 자동으로 실행됩니다.
echo.
pause

