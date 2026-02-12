#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
배포 환경 설정 파일
http://print7123-1.com 도메인용 설정
"""

import os

# 배포 환경 설정
DEPLOYMENT_MODE = os.environ.get('DEPLOYMENT_MODE', 'development')  # 'development' or 'production'
DOMAIN = os.environ.get('DOMAIN', 'http://print7123-1.com')
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))

# 프로덕션 모드 설정
IS_PRODUCTION = DEPLOYMENT_MODE == 'production'

# 보안 설정
SECRET_KEY = os.environ.get('SECRET_KEY', 'onnuri-print-enhanced-2024-production-key-change-this')

# 데이터베이스 설정
DB_PATH = os.environ.get('DB_PATH', 'instance/onnuri_print_enhanced.db')

# 업로드 폴더 설정
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB

# 이메일 설정 (환경 변수에서 가져오거나 기본값 사용)
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.naver.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'print7123@naver.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')

# 로깅 설정
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO' if IS_PRODUCTION else 'DEBUG')
LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log' if IS_PRODUCTION else None)

# 세션 설정
SESSION_COOKIE_SECURE = IS_PRODUCTION  # HTTPS에서만 쿠키 전송
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CORS 설정 (필요한 경우)
ALLOWED_ORIGINS = [
    'http://print7123-1.com',
    'https://print7123-1.com',
    'http://www.print7123-1.com',
    'https://www.print7123-1.com',
]

# 배포 정보 출력
if __name__ == '__main__':
    print("=" * 60)
    print("배포 환경 설정")
    print("=" * 60)
    print(f"배포 모드: {DEPLOYMENT_MODE}")
    print(f"프로덕션 모드: {IS_PRODUCTION}")
    print(f"도메인: {DOMAIN}")
    print(f"호스트: {HOST}")
    print(f"포트: {PORT}")
    print(f"로그 레벨: {LOG_LEVEL}")
    print("=" * 60)

