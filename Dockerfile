# Python 3.9 기반 이미지
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p instance uploads static/portfolio static/brochures static/service_images

# 환경 변수 설정
ENV DEPLOYMENT_MODE=production
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 5000

# 서버 실행
CMD ["python", "app_enhanced_작동중.py"]

