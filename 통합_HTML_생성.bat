@echo off
chcp 65001
title 통합 HTML 파일 생성 (최종 개선 버전)

cd /d "%~dp0"
python 통합_HTML_생성_최종.py

if %errorlevel% neq 0 (
    echo.
    echo [오류] 통합 HTML 파일 생성 중 오류가 발생했습니다.
    echo        Python이 설치되어 있고 PATH에 추가되었는지 확인하세요.
    echo.
) else (
    echo.
    echo ========================================
    echo   통합 HTML 파일 생성이 완료되었습니다.
    echo ========================================
    echo.
)

pause

