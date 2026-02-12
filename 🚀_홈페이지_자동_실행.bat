@echo off
chcp 65001
title 홈페이지 자동 실행 - 서버 자동 시작

echo.
echo ========================================
echo   홈페이지 자동 실행
echo   서버 자동 시작 포함
echo ========================================
echo.

REM 작업 폴더로 이동
cd /d "%~dp0"
echo [1/4] 작업 폴더: %CD%
echo.

REM 서버 실행 여부 확인
echo [2/4] 서버 실행 상태 확인 중...
netstat -an | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  서버가 실행 중이 아닙니다.
    echo   → 서버를 자동으로 시작합니다...
    echo.
    
    REM 기존 Python 프로세스 종료
    taskkill /F /IM python.exe >nul 2>&1
    taskkill /F /IM pythonw.exe >nul 2>&1
    timeout /t 1 >nul
    
    REM Python 확인
    python --version >nul 2>&1
    if errorlevel 1 (
        echo   ❌ Python이 설치되어 있지 않습니다.
        echo   → Python을 설치하세요: https://www.python.org/
        echo.
        if exist "index_통합.html" (
            echo   통합 HTML 파일을 직접 열겠습니다...
            start "" "index_통합.html"
        ) else (
            echo   ⚠️  index_통합.html 파일이 없습니다.
            echo   → 통합_HTML_생성.bat 파일을 실행하여 생성하세요.
        )
        pause
        exit /b 1
    )
    
    REM 서버 백그라운드로 시작
    echo   → 서버 시작 중... (백그라운드)
    start /B python app_enhanced_작동중.py >nul 2>&1
    
    REM 서버 시작 대기 (최대 10초)
    echo   → 서버 시작 대기 중...
    set /a count=0
    :wait_loop
    timeout /t 1 >nul
    netstat -an | findstr ":5000" | findstr "LISTENING" >nul 2>&1
    if errorlevel 1 (
        set /a count+=1
        if %count% lss 10 (
            echo   → 대기 중... (%count%/10초)
            goto wait_loop
        )
    )
    
    netstat -an | findstr ":5000" | findstr "LISTENING" >nul 2>&1
    if errorlevel 1 (
        echo   ⚠️  서버 시작에 실패했습니다.
        if exist "index_통합.html" (
            echo   → 통합 HTML 파일을 직접 열겠습니다...
            start "" "index_통합.html"
        ) else (
            echo   ⚠️  index_통합.html 파일이 없습니다.
            echo   → 통합_HTML_생성.bat 파일을 실행하여 생성하세요.
        )
        pause
        exit /b 1
    ) else (
        echo   ✅ 서버가 시작되었습니다!
    )
) else (
    echo   ✅ 서버가 이미 실행 중입니다.
)
echo.

REM 브라우저로 홈페이지 열기
echo [3/4] 브라우저로 홈페이지 열기...
echo   → http://localhost:5000 접속 중...
echo.
start "" "http://localhost:5000"

REM 통합 HTML 파일도 함께 열기 (선택사항)
echo [4/4] 통합 HTML 파일 확인 및 열기...
if exist "index_통합.html" (
    echo   ✅ index_통합.html 파일 발견
    echo   → index_통합.html 열기...
    timeout /t 2 >nul
    start "" "index_통합.html"
) else (
    echo   ⚠️  index_통합.html 파일이 없습니다.
    if exist "통합_HTML_생성.bat" (
        echo   → 통합 HTML 파일을 자동으로 생성합니다...
        call "통합_HTML_생성.bat"
        timeout /t 2 >nul
        if exist "index_통합.html" (
            echo   ✅ index_통합.html 파일 생성 완료!
            start "" "index_통합.html"
        ) else (
            echo   ⚠️  통합 HTML 파일 생성에 실패했습니다.
            echo   → 수동으로 통합_HTML_생성.bat를 실행하세요.
        )
    ) else (
        echo   ⚠️  통합_HTML_생성.bat 파일이 없습니다.
    )
)

echo.
echo ========================================
echo   ✅ 완료!
echo ========================================
echo.
echo   서버 주소: http://localhost:5000
echo   통합 HTML: index_통합.html
echo.
echo   서버를 중지하려면:
echo   → 작업 관리자에서 python.exe 프로세스를 종료하거나
echo   → 🚀_서버_시작_최종분.bat 창을 닫으세요
echo.
echo   이 창은 5초 후 자동으로 닫힙니다...
timeout /t 5 >nul

