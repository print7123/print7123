# Railway 배포 상세 가이드
## 온누리인쇄나라 서버 Railway 배포

Railway는 가장 간단하고 무료로 시작할 수 있는 클라우드 플랫폼입니다.

---

## 🚀 빠른 시작 (5분)

### 1단계: GitHub에 코드 업로드

#### Git 초기화 (처음인 경우)
```bash
cd "홈페이지_최종분_26.02.11"
git init
git add .
git commit -m "Initial commit for Railway deployment"
```

#### GitHub 저장소 생성
1. https://github.com 접속
2. "New repository" 클릭
3. 저장소 이름: `onnuri-print-shop`
4. Public 또는 Private 선택
5. "Create repository" 클릭

#### 코드 업로드
```bash
git remote add origin https://github.com/yourusername/onnuri-print-shop.git
git branch -M main
git push -u origin main
```

### 2단계: Railway에 배포

1. **Railway 가입**
   - https://railway.app 접속
   - "Login" → "GitHub" 선택
   - GitHub 계정으로 로그인

2. **프로젝트 생성**
   - "Start a New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - GitHub 저장소 선택 (`onnuri-print-shop`)

3. **자동 배포**
   - Railway가 자동으로 코드를 감지하고 배포 시작
   - 배포 완료까지 2-3분 소요

### 3단계: 환경 변수 설정

Railway 대시보드 → 프로젝트 → Variables 탭:

```
DEPLOYMENT_MODE=production
DOMAIN=https://your-app.railway.app
HOST=0.0.0.0
PORT=5000
SECRET_KEY=your-random-secret-key-here
MAIL_SERVER=smtp.naver.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=print7123@naver.com
MAIL_PASSWORD=your-email-password
```

### 4단계: 도메인 설정 (선택사항)

1. Railway 대시보드 → Settings → Domains
2. "Custom Domain" 클릭
3. 도메인 입력: `print7123-1.com`
4. DNS 설정:
   - 타입: `CNAME`
   - 이름: `print7123-1.com`
   - 값: `your-app.railway.app`

---

## 📋 Railway 설정 파일

### `railway.json` (이미 생성됨)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app_enhanced_작동중.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 🔧 문제 해결

### 배포 실패
1. **로그 확인**: Railway 대시보드 → Deployments → Logs
2. **Python 버전 확인**: `runtime.txt` 파일 확인
3. **의존성 확인**: `requirements.txt` 확인

### 서버가 시작되지 않음
1. **포트 확인**: Railway는 자동으로 PORT 환경 변수 설정
2. **환경 변수 확인**: 모든 필수 변수 설정 확인
3. **로그 확인**: 오류 메시지 확인

### 데이터베이스 오류
1. **경로 확인**: Railway는 임시 파일 시스템 사용
2. **영구 저장소**: Railway의 Volume 기능 사용 고려

---

## 💰 비용

### 무료 플랜
- 월 $5 크레딧
- 충분한 트래픽 처리 가능
- 24시간 구동

### 유료 플랜
- $5/월: 더 많은 리소스
- $10/월: 프로덕션 권장

---

## 🔄 자동 배포

GitHub에 push하면 자동으로 재배포됩니다:

```bash
git add .
git commit -m "Update"
git push
```

Railway가 자동으로 감지하고 배포합니다.

---

## 📊 모니터링

- **대시보드**: 실시간 로그, 메트릭 확인
- **알림**: 배포 성공/실패 알림 설정
- **로그**: 상세한 로그 확인

---

**Railway로 쉽게 클라우드 배포 완료!** 🚀

