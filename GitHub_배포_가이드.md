# GitHub Push를 통한 클라우드 배포 가이드
## 온누리인쇄나라 서버 배포

GitHub에 코드를 업로드하고 클라우드에 자동 배포하는 방법입니다.

---

## 📋 전체 과정 요약

1. **GitHub 계정 생성** (없는 경우)
2. **GitHub 저장소 생성**
3. **로컬에서 Git 초기화**
4. **코드 업로드 (Git Push)**
5. **Railway/Render에 연결하여 자동 배포**

---

## 🚀 1단계: GitHub 계정 및 저장소 준비

### GitHub 계정 생성 (없는 경우)
1. https://github.com 접속
2. "Sign up" 클릭
3. 이메일, 비밀번호 입력
4. 이메일 인증 완료

### GitHub 저장소 생성
1. GitHub 로그인 후 우측 상단 "+" → "New repository" 클릭
2. 저장소 정보 입력:
   - **Repository name**: `onnuri-print-shop`
   - **Description**: `온누리인쇄나라 홈페이지 서버`
   - **Public** 또는 **Private** 선택
   - **Initialize this repository with** 체크 해제 (이미 파일이 있으므로)
3. "Create repository" 클릭
4. 저장소 URL 복사 (예: `https://github.com/yourusername/onnuri-print-shop.git`)

---

## 💻 2단계: 로컬에서 Git 설정

### Git 설치 확인
Windows 명령 프롬프트(CMD) 또는 PowerShell에서:
```bash
git --version
```

**Git이 설치되어 있지 않다면:**
1. https://git-scm.com/download/win 접속
2. 다운로드 및 설치
3. 설치 시 기본 옵션으로 진행

### Git 사용자 정보 설정 (처음 사용하는 경우)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## 📁 3단계: 프로젝트 폴더에서 Git 초기화

### 명령 프롬프트 열기
1. `홈페이지_최종분_26.02.11` 폴더로 이동
2. 폴더 내에서 우클릭 → "터미널에서 열기" 또는 "Open in Terminal"
   - 또는 `Shift + 우클릭` → "PowerShell 창 여기서 열기"

### Git 초기화 및 첫 커밋
```bash
# 현재 디렉토리 확인
cd "C:\Users\rdhaj\Downloads\홈페이지 원파일   계산 작동함 25.12.22\홈페이지_최종분_26.02.11"

# Git 초기화
git init

# 모든 파일 추가
git add .

# 첫 커밋
git commit -m "Initial commit: 온누리인쇄나라 서버 배포 준비"

# GitHub 저장소 연결 (yourusername을 실제 사용자명으로 변경)
git remote add origin https://github.com/yourusername/onnuri-print-shop.git

# 기본 브랜치를 main으로 설정
git branch -M main

# GitHub에 업로드
git push -u origin main
```

---

## 🔐 4단계: GitHub 인증

### Personal Access Token 생성 (필요한 경우)
GitHub에서 비밀번호 대신 토큰 사용:

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)" 클릭
3. 설정:
   - **Note**: `Railway Deployment`
   - **Expiration**: `90 days` (또는 원하는 기간)
   - **Scopes**: `repo` 체크 (전체 권한)
4. "Generate token" 클릭
5. **토큰 복사** (한 번만 표시됨!)

### Push 시 인증
```bash
# 사용자명: GitHub 사용자명
# 비밀번호: Personal Access Token (비밀번호 아님!)
```

또는 Git Credential Manager 사용:
```bash
git config --global credential.helper manager-core
```

---

## ☁️ 5단계: Railway에 배포 (자동 배포)

### Railway 가입 및 프로젝트 생성
1. https://railway.app 접속
2. "Login" → "GitHub" 선택
3. GitHub 계정으로 로그인 및 권한 승인

4. Railway 대시보드에서:
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - `onnuri-print-shop` 저장소 선택
   - Railway가 자동으로 배포 시작!

### 환경 변수 설정
Railway 대시보드 → 프로젝트 → Variables 탭에서 추가:

```
DEPLOYMENT_MODE=production
DOMAIN=https://your-app.railway.app
HOST=0.0.0.0
PORT=5000
SECRET_KEY=your-random-secret-key-change-this
MAIL_SERVER=smtp.naver.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=print7123@naver.com
MAIL_PASSWORD=your-email-password
```

### 배포 확인
- Railway 대시보드 → Deployments 탭
- "View Logs"로 배포 상태 확인
- 배포 완료 후 제공되는 URL로 접속 테스트

---

## 🔄 6단계: 코드 업데이트 및 재배포

### 코드 수정 후 재배포
```bash
# 변경사항 확인
git status

# 변경된 파일 추가
git add .

# 커밋
git commit -m "업데이트 내용 설명"

# GitHub에 업로드 (자동으로 Railway가 재배포)
git push
```

**Railway가 자동으로 감지하고 재배포합니다!**

---

## 🌐 7단계: 도메인 연결 (선택사항)

### Railway에서 도메인 설정
1. Railway 대시보드 → Settings → Domains
2. "Custom Domain" 클릭
3. 도메인 입력: `print7123-1.com`
4. DNS 설정 안내 확인

### DNS 설정
도메인 관리 페이지에서:
- **타입**: `CNAME`
- **이름**: `print7123-1.com` (또는 `www`)
- **값**: `your-app.railway.app` (Railway에서 제공)

---

## 📝 자주 사용하는 Git 명령어

### 기본 명령어
```bash
# 상태 확인
git status

# 변경사항 확인
git diff

# 모든 파일 추가
git add .

# 특정 파일만 추가
git add 파일명.py

# 커밋
git commit -m "커밋 메시지"

# GitHub에 업로드
git push

# 최신 코드 가져오기
git pull
```

### 문제 해결
```bash
# 원격 저장소 확인
git remote -v

# 원격 저장소 변경
git remote set-url origin https://github.com/yourusername/onnuri-print-shop.git

# 강제 업로드 (주의!)
git push -f origin main
```

---

## 🚨 문제 해결

### "fatal: not a git repository"
```bash
# Git이 초기화되지 않음
git init
```

### "fatal: remote origin already exists"
```bash
# 기존 원격 저장소 제거 후 재추가
git remote remove origin
git remote add origin https://github.com/yourusername/onnuri-print-shop.git
```

### "Authentication failed"
```bash
# Personal Access Token 사용 확인
# 또는 Git Credential Manager 재설정
git config --global credential.helper manager-core
```

### "Large files" 오류
```bash
# .gitignore 파일 확인
# 큰 파일은 제외하거나 Git LFS 사용
```

### Railway 배포 실패
1. Railway 대시보드 → Logs 확인
2. 환경 변수 확인
3. `requirements.txt` 확인
4. Python 버전 확인 (`runtime.txt`)

---

## ✅ 체크리스트

배포 전 확인사항:
- [ ] Git 설치 완료
- [ ] GitHub 계정 생성
- [ ] GitHub 저장소 생성
- [ ] `.gitignore` 파일 확인 (민감한 정보 제외)
- [ ] `requirements.txt` 최신 상태
- [ ] `runtime.txt` Python 버전 확인
- [ ] 환경 변수 준비 (SECRET_KEY, 이메일 등)
- [ ] Railway 계정 생성
- [ ] Railway-GitHub 연결 완료

---

## 📊 배포 후 확인

### 서버 상태 확인
1. Railway 대시보드 → Metrics
2. CPU, 메모리 사용량 확인
3. 로그 확인

### 웹사이트 접속 테스트
1. Railway에서 제공하는 URL로 접속
2. 모든 페이지 테스트
3. 관리자 로그인 테스트

---

## 💡 팁

### 자동 배포 설정
- GitHub에 push하면 자동으로 Railway가 재배포
- 배포 알림 설정 가능

### 백업
- GitHub에 코드가 백업됨
- 언제든지 이전 버전으로 복구 가능

### 협업
- 여러 사람이 같은 저장소에서 작업 가능
- 변경사항 추적 가능

---

**이제 GitHub Push로 쉽게 배포할 수 있습니다!** 🚀

