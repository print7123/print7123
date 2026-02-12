#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSGI Entry Point for Production Deployment
프로덕션 배포용 WSGI 진입점
gunicorn, uwsgi, waitress 등과 함께 사용
"""

import os
import sys

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 배포 모드 설정
os.environ['DEPLOYMENT_MODE'] = 'production'
os.environ['DOMAIN'] = 'http://print7123-1.com'

# Flask 앱 import
from app_enhanced_작동중 import app

# WSGI 애플리케이션 객체
application = app

if __name__ == '__main__':
    # 직접 실행 시 (테스트용)
    app.run(host='0.0.0.0', port=5000, debug=False)

