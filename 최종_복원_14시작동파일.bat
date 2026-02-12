@echo off
chcp 65001
title 최종 복원 - 14시 작동 파일

echo.
echo ========================================
echo   최종 복원 - 14시 작동 파일
echo ========================================
echo.

REM 현재 폴더 확인
cd /d "%~dp0"
echo [1/5] 현재 작업 폴더: %CD%
echo.

REM Python 스크립트 실행 (우선)
if exist "최종_복원_14시작동파일.py" (
    echo [2/5] Python 스크립트로 복원 실행...
    python "최종_복원_14시작동파일.py"
    if errorlevel 1 (
        echo.
        echo ⚠️  Python 스크립트 실행 실패. 배치 파일로 복원 시도...
        goto batch_restore
    ) else (
        echo.
        echo ========================================
        echo   ✅ 복원 완료!
        echo ========================================
        pause
        exit /b 0
    )
) else (
    echo ⚠️  Python 스크립트가 없습니다. 배치 파일로 복원 시도...
    goto batch_restore
)

:batch_restore
REM 백업 폴더 확인
set "BACKUP_FOLDER=%~dp0..\현재작동파일_백업_1\현재작동파일_백업_20250913_204500"
if not exist "%BACKUP_FOLDER%" (
    echo   ❌ 백업 폴더를 찾을 수 없습니다: %BACKUP_FOLDER%
    echo.
    pause
    exit /b 1
)
echo [2/5] 백업 폴더 확인: %BACKUP_FOLDER%
echo   ✅ 백업 폴더 발견
echo.

REM 기존 파일 백업
echo [3/5] 기존 파일 백업 중...
set "BACKUP_DEST=%~dp0백업_복원전_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "BACKUP_DEST=!BACKUP_DEST: =0!"
if not exist "%BACKUP_DEST%" (
    mkdir "%BACKUP_DEST%"
    if exist "app_enhanced_작동중.py" copy /Y "app_enhanced_작동중.py" "%BACKUP_DEST%\" >nul 2>&1
    if exist "templates" xcopy /E /I /Y "templates" "%BACKUP_DEST%\templates\" >nul 2>&1
    if exist "static" xcopy /E /I /Y "static" "%BACKUP_DEST%\static\" >nul 2>&1
    echo   ✅ 백업 완료: %BACKUP_DEST%
) else (
    echo   ⚠️  백업 폴더가 이미 존재합니다.
)
echo.

REM 파일 복원
echo [4/5] 파일 복원 중...
echo   → app_enhanced_작동중.py 복원...
if exist "%BACKUP_FOLDER%\app_enhanced_작동중.py" (
    copy /Y "%BACKUP_FOLDER%\app_enhanced_작동중.py" "app_enhanced_작동중.py" >nul 2>&1
    if errorlevel 1 (
        echo   ❌ app_enhanced_작동중.py 복원 실패
    ) else (
        echo   ✅ app_enhanced_작동중.py 복원 완료
    )
) else (
    echo   ⚠️  app_enhanced_작동중.py 없음
)

echo   → templates 폴더 복원...
if exist "%BACKUP_FOLDER%\templates" (
    if exist "templates" rmdir /S /Q "templates" >nul 2>&1
    xcopy /E /I /Y "%BACKUP_FOLDER%\templates\*" "templates\" >nul 2>&1
    echo   ✅ templates 폴더 복원 완료
) else (
    echo   ⚠️  templates 폴더가 없습니다.
)

echo   → static 폴더 복원...
if exist "%BACKUP_FOLDER%\static" (
    if exist "static" rmdir /S /Q "static" >nul 2>&1
    xcopy /E /I /Y "%BACKUP_FOLDER%\static\*" "static\" >nul 2>&1
    echo   ✅ static 폴더 복원 완료
) else (
    echo   ⚠️  static 폴더가 없습니다.
)

echo   → requirements.txt 복원...
if exist "%BACKUP_FOLDER%\requirements.txt" (
    copy /Y "%BACKUP_FOLDER%\requirements.txt" "requirements.txt" >nul 2>&1
    echo   ✅ requirements.txt 복원 완료
)

echo   → email_config.py 복원...
if exist "%BACKUP_FOLDER%\email_config.py" (
    copy /Y "%BACKUP_FOLDER%\email_config.py" "email_config.py" >nul 2>&1
    echo   ✅ email_config.py 복원 완료
)

echo   → instance 폴더 복원...
if exist "%BACKUP_FOLDER%\instance" (
    if not exist "instance" mkdir "instance"
    xcopy /E /I /Y "%BACKUP_FOLDER%\instance\*" "instance\" >nul 2>&1
    echo   ✅ instance 폴더 복원 완료
)
echo.

REM 복원 확인
echo [5/5] 복원 확인 중...
if exist "app_enhanced_작동중.py" (
    echo   ✅ app_enhanced_작동중.py 확인
) else (
    echo   ❌ app_enhanced_작동중.py 없음
)
if exist "templates\index.html" (
    echo   ✅ templates\index.html 확인
) else (
    echo   ❌ templates\index.html 없음
)
if exist "static\js\main.js" (
    echo   ✅ static\js\main.js 확인
) else (
    echo   ❌ static\js\main.js 없음
)
echo.

echo ========================================
echo   ✅ 복원 완료!
echo ========================================
echo.
echo   복원된 파일:
echo   - app_enhanced_작동중.py
echo   - templates/ 폴더
echo   - static/ 폴더
echo   - requirements.txt
echo   - email_config.py
echo   - instance/ 폴더
echo.
echo   서버를 시작하려면:
echo   → 🚀_서버_시작_최종분.bat 파일을 실행하세요
echo.
pause
