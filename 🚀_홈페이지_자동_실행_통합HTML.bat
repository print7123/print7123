@echo off
chcp 65001
title 홈페이지 자동 실행 - 통합 HTML (서버 자동 시작)

echo.
echo ========================================
echo   통합 HTML 자동 실행
echo   서버 자동 시작 포함
echo ========================================
echo.

REM 작업 폴더로 이동
cd /d "%~dp0"
echo [1/4] 작업 폴더: %CD%
echo.

REM 통합 HTML 파일 확인 및 생성
echo [2/4] 통합 HTML 파일 확인 중...
if exist "index_통합.html" (
    echo   ✅ index_통합.html 파일 발견
) else (
    echo   ⚠️  index_통합.html 파일이 없습니다.
    echo   → 통합 HTML 파일을 자동으로 생성합니다...
    echo.
    
    REM Python 확인
    python --version >nul 2>&1
    if errorlevel 1 (
        echo   ❌ Python이 설치되어 있지 않습니다.
        echo   → 통합 HTML 파일을 생성할 수 없습니다.
        echo   → 서버만 시작하겠습니다...
        goto server_start
    )
    
    REM 통합 HTML 생성 스크립트 직접 실행
    if exist "통합_HTML_생성_최종.py" (
        echo   → 통합_HTML_생성_최종.py 실행 중...
        python "통합_HTML_생성_최종.py" 2>&1
        echo.
        
        REM 파일 생성 확인 (최대 30초 대기)
        set /a count=0
        :wait_file
        if exist "index_통합.html" (
            echo   ✅ index_통합.html 파일 생성 완료!
            goto file_ready
        ) else (
            set /a count+=1
            if %count% lss 30 (
                timeout /t 1 >nul
                echo   → 파일 생성 대기 중... (%count%/30초)
                goto wait_file
            )
        )
        echo   ⚠️  통합 HTML 파일 생성에 실패했습니다.
        echo   → 수동으로 통합_HTML_생성.bat를 실행하세요.
        :file_ready
    ) else (
        echo   ⚠️  통합_HTML_생성_최종.py 파일이 없습니다.
    )
)
echo.

REM 서버 실행 여부 확인
:server_start
echo [3/4] 서버 실행 상태 확인 중...
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
        echo   → 서버를 시작할 수 없습니다.
        goto open_files
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
        echo   → 통합 HTML 파일만 열겠습니다 (서버 기능 제한)
    ) else (
        echo   ✅ 서버가 시작되었습니다!
    )
) else (
    echo   ✅ 서버가 이미 실행 중입니다.
)
echo.

REM 파일 열기
:open_files
echo [4/4] 파일 열기...
if exist "index_통합.html" (
    echo   → index_통합.html 열기...
    start "" "index_통합.html"
) else (
    echo   ⚠️  index_통합.html 파일이 없습니다.
)

REM 서버 주소도 브라우저로 열기
timeout /t 2 >nul
echo   → http://localhost:5000 열기...
start "" "http://localhost:5000"

echo.
echo ========================================
echo   ✅ 완료!
echo ========================================
echo.
if exist "index_통합.html" (
    echo   통합 HTML: index_통합.html (서버 없이도 작동)
)
echo   서버 주소: http://localhost:5000 (게시판, Q&A 등 사용 가능)
echo.
echo   서버를 중지하려면:
echo   → 작업 관리자에서 python.exe 프로세스를 종료하세요
echo.
echo   이 창은 5초 후 자동으로 닫힙니다...
timeout /t 5 >nul
