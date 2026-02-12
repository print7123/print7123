@echo off
chcp 65001
title 즉시 복원 - 템플릿 오류 수정

echo.
echo ========================================
echo   즉시 복원 중...
echo ========================================
echo.

cd /d "%~dp0"

REM 백업 폴더에서 templates/index.html 복원
set "BACKUP_FILE=%~dp0..\현재작동파일_백업_1\현재작동파일_백업_20250913_204500\templates\index.html"
set "TARGET_FILE=%~dp0templates\index.html"

if exist "%BACKUP_FILE%" (
    echo [1/2] 백업 파일에서 index.html 복원 중...
    copy /Y "%BACKUP_FILE%" "%TARGET_FILE%" >nul 2>&1
    if errorlevel 1 (
        echo   ❌ 복원 실패
    ) else (
        echo   ✅ index.html 복원 완료
    )
) else (
    echo   ❌ 백업 파일을 찾을 수 없습니다: %BACKUP_FILE%
)

REM static/js/main.js도 복원
set "BACKUP_JS=%~dp0..\현재작동파일_백업_1\현재작동파일_백업_20250913_204500\static\js\main.js"
set "TARGET_JS=%~dp0static\js\main.js"

if exist "%BACKUP_JS%" (
    echo [2/2] 백업 파일에서 main.js 복원 중...
    copy /Y "%BACKUP_JS%" "%TARGET_JS%" >nul 2>&1
    if errorlevel 1 (
        echo   ❌ 복원 실패
    ) else (
        echo   ✅ main.js 복원 완료
    )
)

echo.
echo ========================================
echo   ✅ 복원 완료!
echo ========================================
echo.
echo   서버를 재시작하세요: 🚀_서버_시작_최종분.bat
echo.
pause



