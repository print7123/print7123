@echo off
chcp 65001 >nul
title GitHub 배포 준비

echo ========================================
echo GitHub Push를 통한 배포 준비
echo 온누리인쇄나라 서버
echo ========================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

echo [1/5] Git 설치 확인...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git이 설치되어 있지 않습니다.
    echo.
    echo Git 설치 방법:
    echo 1. https://git-scm.com/download/win 접속
    echo 2. 다운로드 및 설치
    echo 3. 이 스크립트를 다시 실행하세요.
    echo.
    pause
    exit /b 1
)

echo ✅ Git 설치 확인 완료
echo.

echo [2/5] Git 사용자 정보 확인...
git config user.name >nul 2>&1
if errorlevel 1 (
    echo Git 사용자 정보가 설정되지 않았습니다.
    echo.
    set /p git_name="GitHub 사용자명을 입력하세요: "
    set /p git_email="이메일 주소를 입력하세요: "
    git config --global user.name "%git_name%"
    git config --global user.email "%git_email%"
    echo ✅ Git 사용자 정보 설정 완료
) else (
    echo ✅ Git 사용자 정보 확인 완료
    echo    이름: %git config user.name%
    echo    이메일: %git config user.email%
)
echo.

echo [3/5] Git 저장소 초기화 확인...
if not exist ".git" (
    echo Git 저장소를 초기화합니다...
    git init
    echo ✅ Git 저장소 초기화 완료
) else (
    echo ✅ Git 저장소 이미 초기화됨
)
echo.

echo [4/5] 파일 추가 준비...
echo.
echo 다음 파일들이 GitHub에 업로드됩니다:
echo (민감한 정보는 .gitignore에 의해 제외됩니다)
echo.
git status --short
echo.

set /p confirm="GitHub에 업로드하시겠습니까? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo [5/5] GitHub 저장소 정보 입력...
echo.
echo GitHub 저장소 URL을 입력하세요.
echo 예: https://github.com/yourusername/onnuri-print-shop.git
echo.
set /p repo_url="저장소 URL: "

if "%repo_url%"=="" (
    echo ❌ 저장소 URL이 입력되지 않았습니다.
    pause
    exit /b 1
)

echo.
echo 원격 저장소 설정 중...
git remote remove origin 2>nul
git remote add origin "%repo_url%"

if errorlevel 1 (
    echo ⚠️ 원격 저장소 추가 실패 (이미 존재할 수 있음)
)

echo.
echo ========================================
echo 파일 커밋 및 업로드
echo ========================================
echo.

REM 모든 파일 추가
echo 파일 추가 중...
git add .

REM 커밋
echo 커밋 중...
git commit -m "온누리인쇄나라 서버 배포 - %date% %time%"

if errorlevel 1 (
    echo ⚠️ 커밋 실패 (변경사항이 없을 수 있음)
)

REM 브랜치를 main으로 설정
git branch -M main

echo.
echo ========================================
echo GitHub에 업로드 중...
echo ========================================
echo.
echo ⚠️ GitHub 인증이 필요할 수 있습니다.
echo    - 사용자명: GitHub 사용자명
echo    - 비밀번호: Personal Access Token (비밀번호 아님!)
echo.
echo Personal Access Token 생성 방법:
echo 1. GitHub → Settings → Developer settings
echo 2. Personal access tokens → Tokens (classic)
echo 3. Generate new token → repo 권한 선택
echo.

git push -u origin main

if errorlevel 1 (
    echo.
    echo ❌ 업로드 실패
    echo.
    echo 가능한 원인:
    echo 1. GitHub 인증 실패
    echo 2. 저장소 URL 오류
    echo 3. 네트워크 문제
    echo.
    echo 수동으로 업로드하려면:
    echo   git push -u origin main
    echo.
) else (
    echo.
    echo ========================================
    echo ✅ GitHub 업로드 완료!
    echo ========================================
    echo.
    echo 다음 단계:
    echo 1. Railway (https://railway.app) 접속
    echo 2. "New Project" → "Deploy from GitHub repo"
    echo 3. 저장소 선택 → 자동 배포 시작!
    echo.
)

echo.
pause

