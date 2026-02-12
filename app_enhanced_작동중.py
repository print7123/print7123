#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온누리인쇄나라 강화된 웹사이트 - 기존 프로그램 연동
기존 마케팅 시스템, AI 디자인, 블로그 포스팅 시스템과 연동
"""

import os
import sys
import json
import hashlib
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl
import threading
import time
import uuid
import subprocess
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Circle, String
from reportlab.graphics import renderPDF
import io

# 기존 프로그램들 import
try:
    from working_print_shop_marketing import WorkingPrintShopMarketing
    MARKETING_AVAILABLE = True
except ImportError:
    MARKETING_AVAILABLE = False
    print("⚠️ 마케팅 시스템을 찾을 수 없습니다.")

try:
    from ai_cover_designer import AICoverDesigner
    AI_DESIGN_AVAILABLE = True
except ImportError:
    AI_DESIGN_AVAILABLE = False
    print("⚠️ AI 디자인 시스템을 찾을 수 없습니다.")

try:
    from naver_blog_auto_poster import NaverBlogContentGenerator
    BLOG_AVAILABLE = True
except ImportError:
    BLOG_AVAILABLE = False
    print("⚠️ 블로그 포스팅 시스템을 찾을 수 없습니다.")

# Flask 앱 초기화 - 템플릿 경로 명시적 설정
# __file__이 없는 경우를 대비 (exec()로 실행될 때)
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # exec()로 실행될 때는 현재 작업 디렉토리 사용
    script_dir = os.getcwd()

# 템플릿과 static 폴더 경로 설정 (상대 경로도 지원)
template_dir = os.path.join(script_dir, 'templates')
static_dir = os.path.join(script_dir, 'static')

# 폴더가 존재하는지 확인하고, 없으면 여러 경로 시도
if not os.path.exists(template_dir):
    print(f"⚠️ 템플릿 폴더 없음: {template_dir}")
    # 다른 가능한 경로들 시도
    possible_template_dirs = [
        os.path.join(os.getcwd(), 'templates'),
        os.path.join(script_dir, '..', 'templates'),
        os.path.join(os.getcwd(), '현재작동파일_백업_1', '현재작동파일_백업_20250913_204500', 'templates'),
    ]
    for possible_dir in possible_template_dirs:
        abs_possible = os.path.abspath(possible_dir)
        if os.path.exists(abs_possible):
            template_dir = abs_possible
            print(f"   ✅ 템플릿 폴더 발견: {template_dir}")
            break
    else:
        print(f"   ❌ 템플릿 폴더를 찾을 수 없습니다!")

if not os.path.exists(static_dir):
    print(f"⚠️ static 폴더 없음: {static_dir}")
    # 다른 가능한 경로들 시도
    possible_static_dirs = [
        os.path.join(os.getcwd(), 'static'),
        os.path.join(script_dir, '..', 'static'),
        os.path.join(os.getcwd(), '현재작동파일_백업_1', '현재작동파일_백업_20250913_204500', 'static'),
    ]
    for possible_dir in possible_static_dirs:
        abs_possible = os.path.abspath(possible_dir)
        if os.path.exists(abs_possible):
            static_dir = abs_possible
            print(f"   ✅ static 폴더 발견: {static_dir}")
            break
    else:
        print(f"   ⚠️ static 폴더를 찾을 수 없습니다. 기본값 사용: {static_dir}")

# 최종 경로 확인 및 출력
print(f"📁 스크립트 디렉토리: {script_dir}")
print(f"📁 템플릿 폴더: {template_dir}")
print(f"📁 Static 폴더: {static_dir}")

# 템플릿 폴더 존재 확인
if os.path.exists(template_dir):
    print(f"✅ 템플릿 폴더 존재 확인")
    template_files = [f for f in os.listdir(template_dir) if f.endswith('.html')]
    print(f"   템플릿 파일 개수: {len(template_files)}")
    if 'index.html' in template_files:
        print(f"   ✅ index.html 존재")
    else:
        print(f"   ❌ index.html 없음")
        print(f"   존재하는 파일: {template_files[:5]}")
else:
    print(f"❌ 템플릿 폴더가 존재하지 않습니다: {template_dir}")
    # 최후의 수단: 스크립트 디렉토리에서 직접 찾기
    script_dir_final = os.path.dirname(os.path.abspath(__file__))
    final_template_dir = os.path.join(script_dir_final, 'templates')
    if os.path.exists(final_template_dir):
        print(f"   ✅ 최종 템플릿 폴더 발견: {final_template_dir}")
        template_dir = final_template_dir
    else:
        raise FileNotFoundError(f"템플릿 폴더를 찾을 수 없습니다. 시도한 경로:\n- {template_dir}\n- {final_template_dir}")

# Flask 앱 생성 - 템플릿 경로를 절대 경로로 변환
template_dir_abs = os.path.abspath(template_dir)
static_dir_abs = os.path.abspath(static_dir)

# 최종 확인
if not os.path.exists(template_dir_abs):
    raise FileNotFoundError(f"템플릿 폴더가 존재하지 않습니다: {template_dir_abs}")

if not os.path.exists(os.path.join(template_dir_abs, 'index.html')):
    raise FileNotFoundError(f"index.html 파일이 템플릿 폴더에 없습니다: {template_dir_abs}")

print(f"📁 Flask 템플릿 폴더 (절대 경로): {template_dir_abs}")
print(f"📁 Flask static 폴더 (절대 경로): {static_dir_abs}")
print(f"✅ 템플릿 경로 최종 확인 완료")

app = Flask(__name__, template_folder=template_dir_abs, static_folder=static_dir_abs)

# 배포 환경 설정 로드
try:
    from deploy_config import (
        DEPLOYMENT_MODE, IS_PRODUCTION, DOMAIN, HOST, PORT,
        SECRET_KEY, SESSION_COOKIE_SECURE,
        SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE
    )
    print(f"✅ 배포 설정 로드 완료: {DEPLOYMENT_MODE} 모드")
    print(f"   도메인: {DOMAIN}")
except ImportError:
    # deploy_config.py가 없으면 기본값 사용
    DEPLOYMENT_MODE = os.environ.get('DEPLOYMENT_MODE', 'development')
    IS_PRODUCTION = DEPLOYMENT_MODE == 'production'
    DOMAIN = os.environ.get('DOMAIN', 'http://localhost:5000')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'onnuri-print-enhanced-2024')
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    print(f"⚠️ deploy_config.py를 찾을 수 없어 기본 설정을 사용합니다.")

app.config['SECRET_KEY'] = SECRET_KEY

# 배포 모드에 따른 설정
if IS_PRODUCTION:
    # 프로덕션 모드: 보안 강화, 캐싱 활성화
    app.config['TEMPLATES_AUTO_RELOAD'] = False  # 프로덕션에서는 자동 리로드 비활성화
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1년 (정적 파일 캐싱)
    app.config['SESSION_COOKIE_SECURE'] = SESSION_COOKIE_SECURE  # HTTPS에서만 쿠키 전송
    app.config['SESSION_COOKIE_HTTPONLY'] = SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = SESSION_COOKIE_SAMESITE
    app.config['PREFERRED_URL_SCHEME'] = 'https'  # HTTPS 우선
    print("🔒 프로덕션 모드: 보안 설정 활성화")
else:
    # 개발 모드: 자동 리로드 설정
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # 템플릿 파일 변경 시 자동 리로드
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐시 방지 (개발 모드)
    print("🔧 개발 모드: 자동 리로드 활성화")

# 데이터베이스 경로 설정 (instance 폴더 우선)
instance_dir = os.path.join(script_dir, 'instance')
os.makedirs(instance_dir, exist_ok=True)
db_path = os.path.join(instance_dir, 'onnuri_print_enhanced.db')
# Windows 경로를 SQLite URI 형식으로 변환 (백슬래시를 슬래시로, 절대 경로는 4개 슬래시)
db_path_normalized = db_path.replace('\\', '/')
if os.path.isabs(db_path):
    # 절대 경로인 경우: sqlite:////C:/path/to/db.db
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path_normalized}'
else:
    # 상대 경로인 경우: sqlite:///path/to/db.db
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path_normalized}'
print(f"📁 데이터베이스 경로: {db_path}")
print(f"📁 SQLAlchemy URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 폴더 경로 설정 (상대 경로 - 나중에 절대 경로로 변환)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PORTFOLIO_FOLDER'] = 'static/portfolio'
app.config['PORTFOLIO_THUMBNAILS'] = 'static/portfolio/thumbnails'
app.config['BROCHURE_FOLDER'] = 'static/brochures'
app.config['BROCHURE_THUMBNAILS'] = 'static/brochures/thumbnails'
app.config['SERVICE_IMAGE_FOLDER'] = 'static/service_images'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB (최대 파일 크기)

# 카카오톡 알림톡 API 설정 (무료)
app.config['KAKAO_REST_API_KEY'] = os.environ.get('KAKAO_REST_API_KEY', '')  # 카카오 REST API 키
app.config['KAKAO_ADMIN_KEY'] = os.environ.get('KAKAO_ADMIN_KEY', '')  # 카카오 Admin 키 (알림톡용)
app.config['KAKAO_TEMPLATE_ID'] = os.environ.get('KAKAO_TEMPLATE_ID', '')  # 알림톡 템플릿 ID
app.config['KAKAO_CHANNEL_LINK'] = 'https://pf.kakao.com/_kjRIj'  # 카카오톡 채널 링크 (무료 대안)

# 홈페이지 최적화 설정
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1년 (정적 파일 캐싱)
app.config['TEMPLATES_AUTO_RELOAD'] = True  # 템플릿 자동 리로드
app.config['ALLOWED_EXTENSIONS'] = {
    # 이미지 파일
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif', 'svg', 'ico',
    # 문서 파일
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf',
    # 디자인 파일
    'ai', 'eps', 'psd', 'indd', 'sketch',
    # 압축 파일
    'zip', 'rar', '7z'
}
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif', 'svg', 'ico'
}
app.config['ALLOWED_BROCHURE_EXTENSIONS'] = {
    # 이미지 파일
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif', 'svg',
    # 문서 파일
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf',
    # 디자인 파일
    'ai', 'eps', 'psd', 'indd', 'sketch',
    # 압축 파일
    'zip', 'rar', '7z'
}

# 이메일 설정 (네이버 메일)
# email_config.py 파일에서 설정을 불러옵니다
try:
    from email_config import (
        MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, 
        MAIL_USERNAME, MAIL_PASSWORD, is_password_set
    )
    app.config['MAIL_SERVER'] = MAIL_SERVER
    app.config['MAIL_PORT'] = MAIL_PORT
    app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
    app.config['MAIL_USERNAME'] = MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
    
    # 비밀번호 설정 확인
    if not is_password_set():
        print("=" * 80)
        print("⚠️ 이메일 비밀번호가 설정되지 않았습니다!")
        print("=" * 80)
        print("📝 설정 방법:")
        print("   1. email_config.py 파일을 엽니다")
        print("   2. MAIL_PASSWORD = 'your-app-password' 부분을 찾습니다")
        print("   3. 'your-app-password'를 실제 네이버 앱 비밀번호로 변경합니다")
        print("   4. 네이버 메일 → 환경설정 → 보안 → 2단계 인증 → 앱 비밀번호 생성")
        print("=" * 80)
    else:
        print("✅ 이메일 설정이 올바르게 로드되었습니다.")
        print(f"   발신자: {MAIL_USERNAME}")
        print(f"   SMTP 서버: {MAIL_SERVER}:{MAIL_PORT}")
except ImportError:
    # email_config.py가 없으면 기본값 사용
    print("⚠️ email_config.py 파일을 찾을 수 없습니다. 기본 설정을 사용합니다.")
    app.config['MAIL_SERVER'] = 'smtp.naver.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'print7123@naver.com'
    app.config['MAIL_PASSWORD'] = 'your-app-password'
    print("   email_config.py 파일을 생성하여 이메일 설정을 관리하세요.")
except Exception as e:
    print(f"⚠️ email_config.py 로드 중 오류: {e}")
    # 오류 발생 시 기본값 사용
    app.config['MAIL_SERVER'] = 'smtp.naver.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'print7123@naver.com'
    app.config['MAIL_PASSWORD'] = 'your-app-password'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Jinja2 커스텀 필터 추가
@app.template_filter('from_json')
def from_json_filter(value):
    """JSON 문자열을 파이썬 객체로 변환"""
    import json
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        if value.startswith('[') or value.startswith('{'):
            return json.loads(value)
        else:
            # 단일 파일 경로인 경우 (기존 호환성)
            return [value]
    except:
        # JSON 파싱 실패 시 단일 파일 경로로 처리
        return [value] if value else []

# 업로드 폴더 생성 (안전하게 - 절대 경로 사용)
try:
    # 현재 작업 디렉토리 기준으로 폴더 생성
    base_dir = script_dir if 'script_dir' in locals() else os.getcwd()
    
    # 상대 경로를 절대 경로로 변환
    upload_folder = app.config['UPLOAD_FOLDER'] if os.path.isabs(app.config['UPLOAD_FOLDER']) else os.path.join(base_dir, app.config['UPLOAD_FOLDER'])
    portfolio_folder = app.config['PORTFOLIO_FOLDER'] if os.path.isabs(app.config['PORTFOLIO_FOLDER']) else os.path.join(base_dir, app.config['PORTFOLIO_FOLDER'])
    portfolio_thumbnails = app.config['PORTFOLIO_THUMBNAILS'] if os.path.isabs(app.config['PORTFOLIO_THUMBNAILS']) else os.path.join(base_dir, app.config['PORTFOLIO_THUMBNAILS'])
    brochure_folder = app.config['BROCHURE_FOLDER'] if os.path.isabs(app.config['BROCHURE_FOLDER']) else os.path.join(base_dir, app.config['BROCHURE_FOLDER'])
    brochure_thumbnails = app.config['BROCHURE_THUMBNAILS'] if os.path.isabs(app.config['BROCHURE_THUMBNAILS']) else os.path.join(base_dir, app.config['BROCHURE_THUMBNAILS'])
    service_image_folder = app.config['SERVICE_IMAGE_FOLDER'] if os.path.isabs(app.config['SERVICE_IMAGE_FOLDER']) else os.path.join(base_dir, app.config['SERVICE_IMAGE_FOLDER'])
    
    # 폴더 생성
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(portfolio_folder, exist_ok=True)
    os.makedirs(portfolio_thumbnails, exist_ok=True)
    os.makedirs(brochure_folder, exist_ok=True)
    os.makedirs(brochure_thumbnails, exist_ok=True)
    os.makedirs(service_image_folder, exist_ok=True)
    
    # 설정 업데이트 (절대 경로로 저장하여 나중에 접근 시에도 정확한 경로 사용)
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['PORTFOLIO_FOLDER'] = portfolio_folder
    app.config['PORTFOLIO_THUMBNAILS'] = portfolio_thumbnails
    app.config['BROCHURE_FOLDER'] = brochure_folder
    app.config['BROCHURE_THUMBNAILS'] = brochure_thumbnails
    app.config['SERVICE_IMAGE_FOLDER'] = service_image_folder
except Exception as e:
    print(f"⚠️ 폴더 생성 중 오류 (무시 가능): {e}")
    # 오류가 발생해도 기본값 사용

# 기존 프로그램 인스턴스 초기화
marketing_system = None
ai_designer = None
blog_generator = None

if MARKETING_AVAILABLE:
    try:
        marketing_system = WorkingPrintShopMarketing()
        print("✅ 마케팅 시스템 연동 완료")
    except Exception as e:
        print(f"❌ 마케팅 시스템 연동 실패: {e}")

if AI_DESIGN_AVAILABLE:
    try:
        ai_designer = AICoverDesigner()
        print("✅ AI 디자인 시스템 연동 완료")
    except Exception as e:
        print(f"❌ AI 디자인 시스템 연동 실패: {e}")

if BLOG_AVAILABLE:
    try:
        blog_generator = NaverBlogContentGenerator()
        print("✅ 블로그 포스팅 시스템 연동 완료")
    except Exception as e:
        print(f"❌ 블로그 포스팅 시스템 연동 실패: {e}")

# 데이터베이스 모델 (기존 + 확장)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy=True)
    questions = db.relationship('Question', backref='user', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    
    # 인쇄 설정
    print_type = db.Column(db.String(20), nullable=False)
    binding_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(50), nullable=False)
    
    # 견적 정보
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    # 파일 정보
    file_path = db.Column(db.String(500))
    special_requirements = db.Column(db.Text)
    
    # 주문 상태
    status = db.Column(db.String(20), default='견적요청')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 익명 질문 허용
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(500), nullable=True)  # 파일 경로 추가
    is_public = db.Column(db.Boolean, default=True, nullable=True)  # 노출 여부 (기본값: 공개, nullable로 설정)
    password_hash = db.Column(db.String(200), nullable=True)  # 비밀번호 해시 (비노출인 경우, nullable)
    email = db.Column(db.String(120), nullable=True)  # 문의자 이메일 (답변 전송용)
    phone = db.Column(db.String(20), nullable=True)  # 문의자 전화번호 (카카오톡 알림용)
    kakao_name = db.Column(db.String(50), nullable=True)  # 카카오톡 이름/ID
    answer_method = db.Column(db.String(20), nullable=True, default='website')  # 답변 받는 방법: website, email, kakao
    answer = db.Column(db.Text, nullable=True)
    is_answered = db.Column(db.Boolean, default=False)
    answer_sent_email = db.Column(db.Boolean, default=False)  # 이메일 전송 여부
    answer_sent_sms = db.Column(db.Boolean, default=False)  # 카카오톡 전송 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime, nullable=True)

# 새로운 모델들
class MarketingLead(db.Model):
    """마케팅 리드 관리"""
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    search_count = db.Column(db.Integer, default=1)
    first_detected = db.Column(db.DateTime, default=datetime.utcnow)
    last_detected = db.Column(db.DateTime, default=datetime.utcnow)
    converted = db.Column(db.Boolean, default=False)
    converted_at = db.Column(db.DateTime)

class AIDesignRequest(db.Model):
    """AI 디자인 요청 관리"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    design_style = db.Column(db.String(50), nullable=False)
    custom_description = db.Column(db.Text)
    status = db.Column(db.String(20), default='요청중')
    generated_image_path = db.Column(db.String(500))
    final_pdf_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BlogPost(db.Model):
    """블로그 포스트 관리"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='초안')
    posted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Portfolio(db.Model):
    """포트폴리오 관리"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    image_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Brochure(db.Model):
    """리플렛/브로슈어 관리"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 전단지, 리플렛, 브로슈어 등
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    file_type = db.Column(db.String(20))  # pdf, image 등
    file_size = db.Column(db.Integer)  # 파일 크기 (bytes)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class ServiceCategory(db.Model):
    """서비스 카테고리 관리 (코일제본, 와이어링제본, 무선제본, 중철제본, 리플렛, 브로셔 등)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 서비스 이름 (예: 코일제본)
    display_name = db.Column(db.String(100), nullable=False)  # 표시 이름
    description = db.Column(db.Text)  # 설명
    icon = db.Column(db.String(50), default='fas fa-book')  # 아이콘 클래스
    color = db.Column(db.String(20), default='primary')  # 색상 (primary, success, warning, danger 등)
    image_path = db.Column(db.String(500))  # 서비스 이미지 경로
    display_order = db.Column(db.Integer, default=0)  # 표시 순서
    is_active = db.Column(db.Boolean, default=True)  # 활성화 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PortfolioCategory(db.Model):
    """포트폴리오 카테고리 관리 (전단지, 명함, 책자, 포스터, 기타 등)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # 카테고리 이름 (예: 전단지)
    display_order = db.Column(db.Integer, default=0)  # 표시 순서
    is_active = db.Column(db.Boolean, default=True)  # 활성화 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BoardCategory(db.Model):
    """게시판 카테고리 (공지사항, 자유게시판 등)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # 카테고리 이름
    description = db.Column(db.String(200))  # 설명
    display_order = db.Column(db.Integer, default=0)  # 표시 순서
    is_active = db.Column(db.Boolean, default=True)  # 활성화 여부
    is_admin_only = db.Column(db.Boolean, default=False)  # 관리자 전용 여부 (공지사항 등)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('BoardPost', backref='category', lazy=True, cascade='all, delete-orphan')

class BoardPost(db.Model):
    """게시판 게시글"""
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('board_category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 작성자 (익명 허용)
    author_name = db.Column(db.String(100), nullable=False)  # 작성자 이름 (익명일 경우)
    title = db.Column(db.String(200), nullable=False)  # 제목
    content = db.Column(db.Text, nullable=False)  # 내용
    file_path = db.Column(db.String(500), nullable=True)  # 첨부 파일
    view_count = db.Column(db.Integer, default=0)  # 조회수
    is_notice = db.Column(db.Boolean, default=False)  # 공지사항 여부
    is_pinned = db.Column(db.Boolean, default=False)  # 상단 고정 여부
    is_active = db.Column(db.Boolean, default=True)  # 활성화 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 댓글 관계
    comments = db.relationship('BoardComment', backref='post', lazy=True, cascade='all, delete-orphan', order_by='BoardComment.created_at.asc()')

class BoardComment(db.Model):
    """게시판 댓글 (관리자 전용)"""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('board_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 관리자만 작성 가능
    content = db.Column(db.Text, nullable=False)  # 댓글 내용
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_IMAGE_EXTENSIONS']

def generate_order_number():
    return f"ONN{datetime.now().strftime('%Y%m%d%H%M%S')}"

def calculate_price(print_type, binding_type, quantity, pages, size, print_method='single'):
    """정확한 단가표 기반 견적 계산 로직 - 고정된 가격표 (2025.01.02 기준)"""
    
    # 페이지 수에 따른 출력 가격 계산
    def get_print_price(print_type, pages, print_method):
        # 페이지 수 구간별 가격표 - 2025.01.02 공식 가격표 고정
        if pages <= 500:
            price_ranges = {
                'black_white': {'single': 40, 'double': 40},  # 고정: 레이져흑백 500P이하
                'laser_color': {'single': 150, 'double': 150},  # 고정: 레이져칼라 500P이하
                'ink_color': {'single': 70, 'double': 70}  # 고정: 잉크칼라 500P이하
            }
        elif pages <= 5000:
            price_ranges = {
                'black_white': {'single': 38, 'double': 33},  # 고정: 레이져흑백 501-5,000P
                'laser_color': {'single': 115, 'double': 110},  # 고정: 레이져칼라 501-5,000P
                'ink_color': {'single': 66, 'double': 60}  # 고정: 잉크칼라 501-5,000P
            }
        elif pages <= 10000:
            price_ranges = {
                'black_white': {'single': 30, 'double': 25},  # 고정: 레이져흑백 5,001-10,000P
                'laser_color': {'single': 93, 'double': 88},  # 고정: 레이져칼라 5,001-10,000P
                'ink_color': {'single': 55, 'double': 50}  # 고정: 잉크칼라 5,001-10,000P
            }
        elif pages <= 15000:
            price_ranges = {
                'black_white': {'single': 27, 'double': 22},  # 고정: 레이져흑백 10,001-15,000P
                'laser_color': {'single': 82, 'double': 77},  # 고정: 레이져칼라 10,001-15,000P
                'ink_color': {'single': 50, 'double': 45}  # 고정: 잉크칼라 10,001-15,000P
            }
        else:  # 15001페이지 이상
            price_ranges = {
                'black_white': {'single': 25, 'double': 20},  # 고정: 레이져흑백 15,001P이상
                'laser_color': {'single': 72, 'double': 66},  # 고정: 레이져칼라 15,001P이상
                'ink_color': {'single': 45, 'double': 40}  # 고정: 잉크칼라 15,001P이상
            }
        
        return price_ranges.get(print_type, {'single': 40, 'double': 40})[print_method]
    
    # 수량에 따른 제본 가격 계산 - 2025.01.02 공식 가격표 고정
    def get_binding_price(binding_type, quantity):
        if binding_type == 'ring':
            if quantity <= 30:
                return 2200  # 고정: 링제본 1-30부
            elif quantity <= 49:
                return 1650  # 고정: 링제본 31-49부
            elif quantity <= 99:
                return 1430  # 고정: 링제본 50-99부
            else:  # 100부 이상
                return 1100  # 고정: 링제본 100부이상
        elif binding_type == 'perfect':
            if quantity <= 30:
                return 2200  # 고정: 무선제본 1-30부
            elif quantity <= 49:
                return 1100  # 고정: 무선제본 31-49부
            elif quantity <= 99:
                return 770   # 고정: 무선제본 50-99부
            else:  # 100부 이상
                return 770   # 고정: 무선제본 100부이상
        elif binding_type == 'saddle':
            return 330  # 고정: 중철제본 부당 330원
        elif binding_type == 'folding':
            return 500  # 고정: 접지제본 기본 가격
        else:
            return 0
    
    # 총 페이지 수 계산 (페이지 × 수량)
    total_pages = pages * quantity
    
    # 출력 가격 계산 (총 페이지 수 기준)
    unit_print_price = get_print_price(print_type, total_pages, print_method)
    total_print_price = unit_print_price * total_pages
    
    # 제본 가격 계산 (부당 가격)
    unit_binding_price = get_binding_price(binding_type, quantity)
    total_binding_price = unit_binding_price * quantity
    
    # 총 가격 (출력비 + 제본비) - 부가세 포함
    total_price_with_tax = total_print_price + total_binding_price
    
    # 세액 계산 (부가세 10%)
    tax_amount = round(total_price_with_tax * 0.1)
    
    # 총 가격 (부가세 제외) - 합계금액에서 세액 제외
    total_price_without_tax = total_price_with_tax - tax_amount
    
    # 단위 가격 (부가세 제외)
    unit_price = total_price_without_tax / quantity
    
    return {
        'unit_price': unit_price,
        'total_price': total_price_without_tax,  # 부가세 제외된 금액
        'total_price_with_tax': total_price_with_tax,  # 부가세 포함된 금액
        'tax_amount': tax_amount,
        'discount_rate': 0,  # 할인은 제본 가격에 이미 반영됨
        'print_price': total_print_price,
        'binding_price': total_binding_price,
        'unit_print_price': unit_print_price,
        'unit_binding_price': unit_binding_price,
        'pages': pages,
        'total_pages': total_pages
    }

# 라우트들
@app.route('/')
def index():
    """강화된 메인 페이지 - 공개 접근 (익명 사용자도 접근 가능)"""
    try:
        # 기본값 설정
        marketing_stats = {}
        recent_orders = []
        is_admin = False
        portfolio_categories = []
        service_categories = []
        
        # 마케팅 통계 가져오기 (오류 발생 시 빈 딕셔너리 사용)
        try:
            marketing_stats = get_marketing_stats()
        except Exception as e:
            print(f"⚠️ 마케팅 통계 조회 오류 (무시): {e}")
            marketing_stats = {}
        
        # 최근 작업 사례 가져오기 (로그인한 경우만)
        try:
            if current_user.is_authenticated:
                recent_orders = Order.query.order_by(Order.created_at.desc()).limit(6).all()
        except Exception as e:
            print(f"⚠️ 최근 주문 조회 오류 (무시): {e}")
            recent_orders = []
        
        # 관리자 여부 확인 (로그인한 경우만)
        is_authenticated = False
        try:
            is_authenticated = current_user.is_authenticated
            if is_authenticated:
                is_admin = bool(current_user.is_admin)
                print(f"🔐 사용자: {current_user.username}, 관리자 여부: {is_admin}")
            else:
                is_admin = False
                print("🔐 로그인하지 않음")
        except Exception as e:
            print(f"⚠️ 관리자 확인 오류 (무시): {e}")
            import traceback
            traceback.print_exc()
            is_admin = False
            is_authenticated = False
        
        # 포트폴리오 카테고리 가져오기 (오류 발생 시 빈 리스트 사용)
        try:
            portfolio_categories = PortfolioCategory.query.filter_by(is_active=True).order_by(PortfolioCategory.display_order, PortfolioCategory.name).all()
        except Exception as e:
            print(f"⚠️ 포트폴리오 카테고리 조회 오류 (무시): {e}")
            portfolio_categories = []
        
        # 서비스 카테고리 가져오기 (오류 발생 시 빈 리스트 사용)
        try:
            service_categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.display_order, ServiceCategory.name).all()
        except Exception as e:
            print(f"⚠️ 서비스 카테고리 조회 오류 (무시): {e}")
            service_categories = []
        
        # 최신 게시글 가져오기 (오류 발생 시 빈 리스트 사용)
        recent_posts = []
        try:
            recent_posts = BoardPost.query.filter_by(is_active=True).order_by(BoardPost.is_pinned.desc(), BoardPost.created_at.desc()).limit(5).all()
        except Exception as e:
            print(f"⚠️ 최신 게시글 조회 오류 (무시): {e}")
            recent_posts = []
        
        # 템플릿 렌더링
        # Flask 앱이 이미 올바른 템플릿 경로로 초기화되었으므로 바로 렌더링 시도
        try:
            return render_template('index.html', 
                                 marketing_stats=marketing_stats,
                                 recent_orders=recent_orders,
                                 is_admin=is_admin,
                                 is_authenticated=is_authenticated,
                                 portfolio_categories=portfolio_categories,
                                 service_categories=service_categories,
                                 recent_posts=recent_posts)
        except Exception as template_error:
            print(f"❌ 템플릿 렌더링 오류: {template_error}")
            import traceback
            traceback.print_exc()
            # Flask 앱의 템플릿 폴더 확인
            print(f"   Flask 앱 템플릿 폴더: {app.template_folder}")
            print(f"   템플릿 폴더 존재: {os.path.exists(app.template_folder) if app.template_folder else 'None'}")
            if app.template_folder and os.path.exists(app.template_folder):
                files = os.listdir(app.template_folder)
                print(f"   템플릿 폴더 내 파일: {files[:10]}")
            
            # 사용자에게 친화적인 오류 페이지 반환
            return f"""<html><head><meta charset="UTF-8"><title>템플릿 오류</title></head>
<body style="font-family: Arial; padding: 50px; text-align: center;">
<h1>⚠️ 템플릿 오류</h1>
<p>메인 페이지를 불러오는 중 오류가 발생했습니다.</p>
<p><strong>오류 메시지:</strong> {str(template_error)}</p>
<p><strong>템플릿 경로:</strong> {app.template_folder if app.template_folder else '설정되지 않음'}</p>
<p>서버를 재시작해주세요.</p>
<p><a href="/">다시 시도</a></p>
</body></html>""", 500
                             
    except Exception as e:
        print(f"❌ 메인 페이지 로드 오류: {e}")
        import traceback
        traceback.print_exc()
        
        # 기본값으로 렌더링 시도
        try:
            return render_template('index.html', 
                                 marketing_stats={},
                                 recent_orders=[],
                                 is_admin=False,
                                 recent_posts=[],
                                 is_authenticated=False,
                                 portfolio_categories=[],
                                 service_categories=[])
        except Exception as template_error:
            print(f"❌ 템플릿 렌더링 오류: {template_error}")
            # 최소한의 HTML 반환
            return f"""<html><head><meta charset="UTF-8"><title>오류</title></head>
<body>
<h1>서버 오류 발생</h1>
<p>메인 페이지를 불러오는 중 오류가 발생했습니다.</p>
<p>오류 메시지: {str(e)}</p>
<p>템플릿 오류: {str(template_error)}</p>
<p><a href="/">다시 시도</a></p>
</body></html>""", 500

@app.route('/quote', methods=['GET', 'POST'])
def quote():
    """강화된 견적 계산"""
    if request.method == 'POST':
        try:
            data = request.get_json()
        
            # 필수 데이터 검증
            if not data:
                return jsonify({'error': '견적 데이터가 없습니다.'}), 400
            
            required_fields = ['printType', 'bindingType', 'quantity', 'pages']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'{field} 필드가 필요합니다.'}), 400
            
            # 견적 계산
            price_info = calculate_price(
                data['printType'],
                data['bindingType'],
                safe_int_conversion(data['quantity']),
                safe_int_conversion(data['pages']),
                data.get('size', 'A4'),
                data.get('printMethod', 'single')
            )
            
            # 마케팅 리드 생성
            try:
                create_marketing_lead(data)
            except Exception as e:
                print(f"마케팅 리드 생성 오류: {e}")
        
            # 이메일 견적서 전송 (이메일이 제공된 경우)
            if data.get('email'):
                try:
                    send_quote_email(data, price_info)
                except Exception as e:
                    print(f"이메일 전송 오류: {e}")
            
            return jsonify(price_info)
            
        except Exception as e:
            print(f"견적 계산 오류: {e}")
            return jsonify({'error': f'견적 계산 중 오류가 발생했습니다: {str(e)}'}), 500
    
    return render_template('quote.html')

@app.route('/ai-design', methods=['GET', 'POST'])
@login_required
def ai_design():
    """AI 디자인 서비스"""
    if request.method == 'POST':
        title = request.form['title']
        company_name = request.form['company_name']
        design_style = request.form['design_style']
        custom_description = request.form.get('custom_description', '')
        
        # AI 디자인 요청 생성
        design_request = AIDesignRequest(
            user_id=current_user.id,
            title=title,
            company_name=company_name,
            design_style=design_style,
            custom_description=custom_description
        )
        
        db.session.add(design_request)
        db.session.commit()
        
        # AI 디자인 생성 (백그라운드)
        if ai_designer:
            threading.Thread(target=generate_ai_design, args=(design_request.id,)).start()
        
        flash('AI 디자인 요청이 접수되었습니다. 잠시만 기다려주세요.', 'success')
        return redirect(url_for('ai_design_status', request_id=design_request.id))
    
    return render_template('ai_design.html')

@app.route('/ai-design/status/<int:request_id>')
@login_required
def ai_design_status(request_id):
    """AI 디자인 상태 확인"""
    design_request = AIDesignRequest.query.get_or_404(request_id)
    if design_request.user_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('ai_design'))
    
    return render_template('ai_design_status.html', design_request=design_request)

@app.route('/marketing-dashboard')
@login_required
def marketing_dashboard():
    """마케팅 대시보드"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    # 마케팅 통계
    stats = get_marketing_stats()
    
    # 최근 리드
    recent_leads = MarketingLead.query.order_by(MarketingLead.last_detected.desc()).limit(20).all()
    
    # 블로그 포스트 현황
    blog_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(10).all()
    
    return render_template('marketing_dashboard.html',
                         stats=stats,
                         recent_leads=recent_leads,
                         blog_posts=blog_posts)

@app.route('/blog-management')
@login_required
def blog_management():
    """블로그 관리"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blog_management.html', posts=posts)

@app.route('/blog/create-post', methods=['GET', 'POST'])
@login_required
def create_blog_post():
    """블로그 포스트 생성"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        topic = request.form['topic']
        keyword = request.form['keyword']
        content = request.form['content']
        
        # 블로그 포스트 생성
        post = BlogPost(
            title=title,
            content=content,
            topic=topic,
            keyword=keyword,
            status='초안'
        )
        
        db.session.add(post)
        db.session.commit()
        
        # 블로그에 자동 포스팅 (백그라운드)
        if blog_generator:
            threading.Thread(target=post_to_blog, args=(post.id,)).start()
        
        flash('블로그 포스트가 생성되었습니다.', 'success')
        return redirect(url_for('blog_management'))
    
    return render_template('create_blog_post.html')

# 유틸리티 함수들
def get_marketing_stats():
    """마케팅 통계 가져오기"""
    if not marketing_system:
        return {}
    
    try:
        # 마케팅 시스템에서 통계 가져오기
        stats = {
            'total_leads': MarketingLead.query.count(),
            'converted_leads': MarketingLead.query.filter_by(converted=True).count(),
            'top_keywords': db.session.query(MarketingLead.keyword, db.func.count(MarketingLead.id)).group_by(MarketingLead.keyword).order_by(db.func.count(MarketingLead.id).desc()).limit(5).all(),
            'recent_leads': MarketingLead.query.order_by(MarketingLead.last_detected.desc()).limit(5).all()
        }
        return stats
    except Exception as e:
        print(f"마케팅 통계 가져오기 실패: {e}")
        return {}

def create_marketing_lead(data):
    """마케팅 리드 생성"""
    try:
        # 키워드 추출
        keyword = extract_keyword_from_data(data)
        if keyword:
            # 기존 리드 확인
            existing_lead = MarketingLead.query.filter_by(keyword=keyword).first()
            if existing_lead:
                existing_lead.search_count += 1
                existing_lead.last_detected = datetime.utcnow()
            else:
                new_lead = MarketingLead(
                    keyword=keyword,
                    category='quote_request',
                    search_count=1
                )
                db.session.add(new_lead)
            
            db.session.commit()
    except Exception as e:
        print(f"마케팅 리드 생성 실패: {e}")

def send_quote_email(data, price_info):
    """견적서를 이메일로 전송 (직인 포함)"""
    try:
        customer_name = data.get('customerName', '고객님')
        email = data.get('email')
        pages = data.get('pages')
        print_type = data.get('printType')
        binding_type = data.get('bindingType')
        quantity = data.get('quantity')
        
        # 출력 타입 한글 변환
        print_type_map = {
            'black_white': '레이저흑백',
            'laser_color': '레이저칼라',
            'ink_color': '잉크칼라'
        }
        
        # 제본 타입 한글 변환
        binding_type_map = {
            'ring': '링제본',
            'perfect': '무선제본',
            'saddle': '중철제본',
            'folding': '접지'
        }
        
        # 이메일 제목
        subject = f"[온누리인쇄나라] 견적서 - {customer_name}님"
        
        # HTML 이메일 내용 (직인 포함)
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>견적서</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007ACC;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .company-name {{
            font-size: 28px;
            font-weight: bold;
            color: #007ACC;
            margin-bottom: 10px;
        }}
        .quote-title {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .quote-info {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .price-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .price-table th, .price-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        .price-table th {{
            background-color: #007ACC;
            color: white;
            font-weight: bold;
        }}
        .total-price {{
            font-size: 20px;
            font-weight: bold;
            color: #007ACC;
            text-align: right;
        }}
        .contact-info {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .stamp-section {{
            text-align: right;
            margin-top: 40px;
            position: relative;
        }}
        .stamp {{
            display: inline-block;
            width: 120px;
            height: 120px;
            border: 3px solid #dc3545;
            border-radius: 50%;
            position: relative;
            background: linear-gradient(45deg, #fff, #f8f9fa);
        }}
        .stamp-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 14px;
            font-weight: bold;
            color: #dc3545;
            text-align: center;
            line-height: 1.2;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">온누리인쇄나라</div>
        <div class="quote-title">견적서</div>
    </div>
    
    <div class="quote-info">
        <p><strong>고객명:</strong> {customer_name}</p>
        <p><strong>견적일:</strong> 2025년 08월 11일</p>
    </div>
    
    <h3>📋 인쇄 사양</h3>
    <table class="price-table">
        <tr>
            <th>항목</th>
            <th>내용</th>
        </tr>
        <tr>
            <td>페이지 수</td>
            <td>{pages}페이지</td>
        </tr>
        <tr>
            <td>출력 타입</td>
            <td>{print_type_map.get(print_type, print_type)}</td>
        </tr>
        <tr>
            <td>제본 방식</td>
            <td>{binding_type_map.get(binding_type, binding_type)}</td>
        </tr>
        <tr>
            <td>수량</td>
            <td>{quantity}권</td>
        </tr>
    </table>
    
    <h3>💰 가격 내역</h3>
    <table class="price-table">
        <tr>
            <th>항목</th>
            <th>금액</th>
        </tr>
        <tr>
            <td>페이지당 단가</td>
            <td>{price_info['unit_print_price']:,}원</td>
        </tr>
        <tr>
            <td>총 출력 가격</td>
            <td>{price_info['print_price']:,}원</td>
        </tr>
        <tr>
            <td>제본 가격</td>
            <td>{price_info['binding_price']:,}원</td>
        </tr>
        <tr>
            <td>단가 (출력+제본)</td>
            <td>{price_info['unit_price']:,}원</td>
        </tr>
        <tr style="background-color: #e3f2fd;">
            <td><strong>총 가격</strong></td>
            <td class="total-price"><strong>{price_info['total_price']:,}원</strong></td>
        </tr>
    </table>
    
    <div class="contact-info">
        <h4>📞 문의 및 주문</h4>
        <p><strong>전화:</strong> 02-6338-7123</p>
        <p><strong>휴대폰:</strong> 010-2624-7123</p>
        <p><strong>이메일:</strong> print7123@naver.com</p>
        <p><strong>웹사이트:</strong> https://print7123.com/</p>
        <p><strong>영업시간:</strong> 09:30-16:00 (월-금)</p>
    </div>
    
    <div class="stamp-section">
        <div class="stamp">
            <div class="stamp-text">
                온누리인쇄나라<br>
                대표: 김인쇄<br>
                {datetime.now().strftime('%Y.%m.%d')}
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p><strong>※ 안내사항</strong></p>
        <ul>
            <li>기본 80g 복사용지, 부가세 포함</li>
            <li>페이지 수와 수량에 따른 차등 가격 적용</li>
            <li>본 견적서는 7일간 유효합니다</li>
            <li>실제 가격은 최종 확인 후 결정됩니다</li>
        </ul>
        <p style="text-align: center; margin-top: 20px;">
            <strong>감사합니다. 온누리인쇄나라 드림</strong>
        </p>
    </div>
</body>
</html>
        """
        
        # 텍스트 버전 (HTML을 지원하지 않는 이메일 클라이언트용)
        text_content = f"""
안녕하세요, {customer_name}님!

온누리인쇄나라에서 요청하신 견적서를 보내드립니다.

========================================
           견적서
========================================

고객명: {customer_name}
견적일: 2025년 08월 11일

[인쇄 사양]
페이지 수: {pages}페이지
출력 타입: {print_type_map.get(print_type, print_type)}
제본 방식: {binding_type_map.get(binding_type, binding_type)}
수량: {quantity}권

[가격 내역]
페이지당 단가: {price_info['unit_print_price']:,}원
총 출력 가격: {price_info['print_price']:,}원
제본 가격: {price_info['binding_price']:,}원
단가 (출력+제본): {price_info['unit_price']:,}원
총 가격: {price_info['total_price']:,}원

※ 기본 80g 복사용지, 부가세 포함
※ 페이지 수와 수량에 따른 차등 가격 적용

========================================

문의사항이나 주문을 원하시면 언제든 연락주세요!

📞 전화: 02-6338-7123
📱 휴대폰: 010-2624-7123
📧 이메일: print7123@naver.com
🌐 웹사이트: https://print7123.com/

⏰ 영업시간: 09:30-16:00 (월-금)

※ 본 견적서는 7일간 유효합니다.
※ 실제 가격은 최종 확인 후 결정됩니다.

감사합니다.
온누리인쇄나라 드림
        """
        
        # HTML 이메일 발송
        if send_html_email(email, subject, html_content, text_content):
            print(f"✅ 견적서 이메일 전송 성공: {email}")
            return True
        else:
            print(f"❌ 견적서 이메일 전송 실패: {email}")
            return False
            
    except Exception as e:
        print(f"견적서 이메일 전송 오류: {e}")
        return False

def send_html_email(to_email, subject, html_content, text_content):
    """HTML 이메일 발송"""
    try:
        print("=" * 60)
        print("📧 이메일 전송 시도 시작...")
        print(f"   수신자: {to_email}")
        print(f"   제목: {subject}")
        print(f"   발신자: {app.config.get('MAIL_USERNAME', 'N/A')}")
        print(f"   SMTP 서버: {app.config.get('MAIL_SERVER', 'N/A')}:{app.config.get('MAIL_PORT', 'N/A')}")
        
        # SMTP 설정 확인
        mail_username = app.config.get('MAIL_USERNAME', '')
        mail_password = app.config.get('MAIL_PASSWORD', '')
        mail_server = app.config.get('MAIL_SERVER', '')
        mail_port = app.config.get('MAIL_PORT', 587)
        
        if not mail_username:
            print("❌ 이메일 사용자명이 설정되지 않았습니다.")
            print("   app.config['MAIL_USERNAME']을 설정하세요.")
            return False
        
        if not mail_password or mail_password == 'your-app-password':
            print("❌ 이메일 비밀번호가 설정되지 않았습니다.")
            print("   app.config['MAIL_PASSWORD']에 네이버 앱 비밀번호를 설정하세요.")
            print("   네이버 메일 → 환경설정 → 보안 → 2단계 인증 → 앱 비밀번호 생성")
            return False
        
        if not mail_server:
            print("❌ SMTP 서버가 설정되지 않았습니다.")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = mail_username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # 텍스트 버전
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # HTML 버전
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 이메일 발송
        print("   SMTP 서버 연결 시도...")
        context = ssl.create_default_context()
        with smtplib.SMTP(mail_server, mail_port) as server:
            print("   TLS 시작...")
            server.starttls(context=context)
            print("   로그인 시도...")
            server.login(mail_username, mail_password)
            print("   이메일 전송 중...")
            server.send_message(msg)
        
        print(f"✅ 이메일 전송 성공: {to_email}")
        print("=" * 60)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("=" * 60)
        print(f"❌ 이메일 인증 오류: {e}")
        print("=" * 60)
        print("   가능한 원인:")
        print("   1. 이메일 주소 또는 비밀번호가 잘못되었습니다.")
        print("   2. 네이버 앱 비밀번호가 아닌 일반 비밀번호를 사용했습니다.")
        print("      ⚠️ 중요: 네이버는 일반 비밀번호로 SMTP 인증이 불가능합니다!")
        print("      반드시 앱 비밀번호를 사용해야 합니다.")
        print("   3. 2단계 인증이 활성화되지 않았습니다.")
        print("   4. 앱 비밀번호가 만료되었거나 삭제되었습니다.")
        print("=" * 60)
        print("   해결 방법:")
        print("   1. 네이버 메일 → 환경설정 → 보안 → 2단계 인증 활성화")
        print("   2. 앱 비밀번호 생성 (16자리)")
        print("   3. 관리자 대시보드에서 새 앱 비밀번호 설정")
        print("   4. 서버 재시작")
        print("=" * 60)
        print(f"   현재 사용 중인 비밀번호 길이: {len(mail_password)}자")
        print(f"   현재 사용 중인 비밀번호 시작: {mail_password[:3]}***")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False
        
    except smtplib.SMTPException as e:
        print("=" * 60)
        print(f"❌ SMTP 오류: {e}")
        print("   가능한 원인:")
        print("   1. SMTP 서버 주소 또는 포트가 잘못되었습니다.")
        print("   2. 네트워크 연결 문제입니다.")
        print("   3. SMTP 서버가 일시적으로 사용할 수 없습니다.")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ 이메일 전송 오류: {e}")
        print(f"   오류 타입: {type(e).__name__}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

def send_answer_email(to_email, question_title, answer):
    """Q&A 답변을 이메일로 전송 (카카오톡 링크 포함)"""
    try:
        subject = f'[온누리인쇄나라] 문의하신 "{question_title}"에 대한 답변입니다'
        kakao_channel_link = app.config.get('KAKAO_CHANNEL_LINK', 'https://pf.kakao.com/_kjRIj')
        
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Malgun Gothic', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .answer {{ background-color: white; padding: 15px; border-left: 4px solid #007bff; margin-top: 15px; }}
                .kakao-box {{ background-color: #FEE500; padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center; }}
                .kakao-button {{ background-color: #3C1E1E; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>온누리인쇄나라</h2>
                </div>
                <div class="content">
                    <p>안녕하세요.</p>
                    <p>문의하신 <strong>"{question_title}"</strong>에 대한 답변을 드립니다.</p>
                    <div class="answer">
                        {answer.replace(chr(10), '<br>')}
                    </div>
                    <div class="kakao-box">
                        <p style="margin: 0; font-weight: bold; color: #3C1E1E;">💬 카카오톡으로도 문의하실 수 있습니다</p>
                        <a href="{kakao_channel_link}" class="kakao-button" target="_blank">
                            카카오톡 채널로 이동하기
                        </a>
                    </div>
                    <p style="margin-top: 20px;">추가 문의사항이 있으시면 언제든지 연락주세요.</p>
                </div>
                <div class="footer">
                    <p>온누리인쇄나라</p>
                    <p>전화: 02-6338-7123 | 이메일: print7123@naver.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
온누리인쇄나라

안녕하세요.

문의하신 "{question_title}"에 대한 답변을 드립니다.

{answer}

💬 카카오톡으로도 문의하실 수 있습니다
카카오톡 채널: {kakao_channel_link}

추가 문의사항이 있으시면 언제든지 연락주세요.

온누리인쇄나라
전화: 02-6338-7123
이메일: print7123@naver.com
        """
        
        return send_html_email(to_email, subject, html_content, text_content)
        
    except Exception as e:
        print(f"답변 이메일 전송 오류: {e}")
        return False

def send_answer_kakao(phone, question_title, answer):
    """Q&A 답변을 카카오톡 알림톡으로 전송 (무료)"""
    try:
        # 카카오톡 알림톡 API 설정 확인
        kakao_admin_key = app.config.get('KAKAO_ADMIN_KEY', '')
        kakao_template_id = app.config.get('KAKAO_TEMPLATE_ID', '')
        kakao_channel_link = app.config.get('KAKAO_CHANNEL_LINK', 'https://pf.kakao.com/_kjRIj')
        
        # 카카오톡 알림톡 API가 설정되지 않은 경우
        # 이메일로 카카오톡 채널 링크를 포함하여 전송 (무료 대안)
        if not kakao_admin_key or not kakao_template_id:
            print("ℹ️ 카카오톡 알림톡 API가 설정되지 않았습니다.")
            print(f"   카카오톡 채널 링크를 포함한 이메일로 전송합니다: {kakao_channel_link}")
            
            # 전화번호가 있지만 이메일 주소가 없는 경우
            # 고정된 이메일 주소로 전송 (print7123@naver.com)
            # 실제로는 전화번호로 직접 전송할 수 없으므로, 이메일로 알림 전송
            recipient_email = 'print7123@naver.com'  # 고정된 수신 이메일
            
            subject = f'[온누리인쇄나라] 문의하신 "{question_title}"에 대한 답변이 등록되었습니다.'
            html_content = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Malgun Gothic', Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #FEE500; color: #3C1E1E; padding: 20px; text-align: center; }}
                    .content {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                    .answer {{ background-color: white; padding: 15px; border-left: 4px solid #FEE500; margin-top: 15px; }}
                    .kakao-box {{ background-color: #FEE500; padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center; }}
                    .kakao-button {{ background-color: #3C1E1E; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
                    .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>💬 카카오톡 알림 - 온누리인쇄나라</h2>
                    </div>
                    <div class="content">
                        <p>안녕하세요.</p>
                        <p>문의하신 <strong>"{question_title}"</strong>에 대한 답변이 등록되었습니다.</p>
                        <p><strong>등록된 전화번호:</strong> {phone}</p>
                        <div class="answer">
                            <p><strong>답변:</strong></p>
                            <p>{answer.replace(chr(10), '<br>')}</p>
                        </div>
                        <div class="kakao-box">
                            <p style="margin: 0; font-weight: bold; color: #3C1E1E;">💬 카카오톡 채널로 이동하여 확인하세요</p>
                            <a href="{kakao_channel_link}" class="kakao-button">
                                카카오톡 채널로 이동하기
                            </a>
                        </div>
                        <p style="margin-top: 20px;">자세한 내용은 홈페이지 Q&A 게시판에서 확인하실 수 있습니다.</p>
                        <p style="margin-top: 10px; color: #666; font-size: 12px;">
                            <strong>참고:</strong> 카카오톡 알림톡 API가 설정되지 않아 이메일로 전송되었습니다.<br>
                            카카오톡으로 직접 알림을 받으시려면 카카오톡 채널에 친구 추가를 해주세요.
                        </p>
                    </div>
                    <div class="footer">
                        <p>온누리인쇄나라</p>
                        <p>전화: 02-6338-7123 | 이메일: print7123@naver.com</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
온누리인쇄나라 - 카카오톡 알림

안녕하세요.

문의하신 "{question_title}"에 대한 답변이 등록되었습니다.

등록된 전화번호: {phone}

답변:
{answer}

💬 카카오톡 채널로 이동하여 확인하세요
카카오톡 채널: {kakao_channel_link}

자세한 내용은 홈페이지 Q&A 게시판에서 확인하실 수 있습니다.

참고: 카카오톡 알림톡 API가 설정되지 않아 이메일로 전송되었습니다.
카카오톡으로 직접 알림을 받으시려면 카카오톡 채널에 친구 추가를 해주세요.

온누리인쇄나라
전화: 02-6338-7123
이메일: print7123@naver.com
            """
            
            # 이메일로 전송 (카카오톡 채널 링크 포함)
            email_sent = send_html_email(recipient_email, subject, html_content, text_content)
            if email_sent:
                print(f"✅ 카카오톡 알림 (이메일 대체) 전송 성공: {phone} → {recipient_email}")
                return True
            else:
                print(f"⚠️ 카카오톡 알림 (이메일 대체) 전송 실패: {phone}")
                return False
        
        # 카카오톡 알림톡 API 사용 (설정된 경우)
        # 주의: 카카오톡 알림톡은 수신자가 카카오톡 비즈니스 채널에 친구 추가되어 있어야 함
        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {
            'Authorization': f'KakaoAK {kakao_admin_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # 알림톡 메시지 생성
        message = f"[온누리인쇄나라]\n\n문의하신 '{question_title[:30]}'에 대한 답변이 등록되었습니다.\n\n홈페이지에서 확인해주세요.\n\n{kakao_channel_link}"
        
        data = {
            'template_id': kakao_template_id,
            'template_args': json.dumps({
                'question_title': question_title[:30],
                'answer_preview': answer[:50] + '...' if len(answer) > 50 else answer,
                'channel_link': kakao_channel_link
            })
        }
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            print(f"✅ 카카오톡 알림톡 전송 성공: {phone}")
            return True
        else:
            print(f"⚠️ 카카오톡 알림톡 전송 실패: {response.text}")
            # 실패해도 카카오톡 채널 링크는 제공되므로 True 반환
            return True
            
    except Exception as e:
        print(f"카카오톡 알림톡 전송 오류: {e}")
        # 오류 발생 시에도 True 반환 (이메일로 대체 가능)
        return True

def extract_keyword_from_data(data):
    """데이터에서 키워드 추출"""
    keywords = []
    
    # 인쇄 타입에서 키워드 추출
    print_type_map = {
        'black_white': '흑백인쇄',
        'ink_color': '잉크칼라인쇄',
        'laser_color': '레이저칼라인쇄'
    }
    
    binding_type_map = {
        'ring': '링제본',
        'perfect': '무선제본',
        'saddle': '중철제본',
        'folding': '접지제본'
    }
    
    if data.get('printType'):
        keywords.append(print_type_map.get(data['printType'], data['printType']))
    
    if data.get('bindingType'):
        keywords.append(binding_type_map.get(data['bindingType'], data['bindingType']))
    
    return ' '.join(keywords) if keywords else None

def generate_ai_design(request_id):
    """AI 디자인 생성 (백그라운드)"""
    try:
        design_request = AIDesignRequest.query.get(request_id)
        if not design_request or not ai_designer:
            return
        
        # AI 디자인 생성
        result = ai_designer.create_cover_design(
            title=design_request.title,
            company_name=design_request.company_name,
            design_style=design_request.design_style,
            custom_description=design_request.custom_description
        )
        
        if result.get('success'):
            design_request.status = '완료'
            design_request.generated_image_path = result.get('image_path')
            design_request.final_pdf_path = result.get('pdf_path')
        else:
            design_request.status = '실패'
        
        db.session.commit()
        
    except Exception as e:
        print(f"AI 디자인 생성 실패: {e}")
        design_request = AIDesignRequest.query.get(request_id)
        if design_request:
            design_request.status = '실패'
            db.session.commit()

def post_to_blog(post_id):
    """블로그에 포스팅 (백그라운드)"""
    try:
        post = BlogPost.query.get(post_id)
        if not post or not blog_generator:
            return
        
        # 블로그 포스팅
        success = blog_generator.post_to_blog({
            'title': post.title,
            'content': post.content,
            'topic': post.topic,
            'keyword': post.keyword
        })
        
        if success:
            post.status = '발행완료'
            post.posted_at = datetime.utcnow()
        else:
            post.status = '발행실패'
        
        db.session.commit()
        
    except Exception as e:
        print(f"블로그 포스팅 실패: {e}")
        post = BlogPost.query.get(post_id)
        if post:
            post.status = '발행실패'
            db.session.commit()

@app.route('/preview_quote', methods=['POST'])
def preview_quote():
    """견적서 미리보기 (텍스트 기반)"""
    try:
        data = request.get_json()
        
        # 필수 데이터 검증
        if not data:
            return jsonify({'error': '견적 데이터가 없습니다.'}), 400
        
        required_fields = ['printType', 'bindingType', 'quantity', 'pages']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} 필드가 필요합니다.'}), 400
        
        # 견적 계산
        price_info = calculate_price(
            data['printType'],
            data['bindingType'],
            safe_int_conversion(data['quantity']),
            safe_int_conversion(data['pages']),
            data.get('size', 'A4'),
            data.get('printMethod', 'single')
        )
        
        # 텍스트 기반 미리보기 제공
        return jsonify({
            'success': True,
            'preview_image': None,
            'price_info': price_info,
            'fallback': True
        })
        
    except Exception as e:
        print(f"미리보기 생성 오류: {e}")
        return jsonify({'error': '미리보기 생성 중 오류가 발생했습니다.'}), 500

@app.route('/download_quote_pdf', methods=['POST'])
def download_quote_pdf():
    """견적서 PDF 다운로드"""
    try:
        data = request.get_json()
        
        # 필수 데이터 검증
        if not data:
            return jsonify({'error': '견적 데이터가 없습니다.'}), 400
        
        required_fields = ['printType', 'bindingType', 'quantity', 'pages']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} 필드가 필요합니다.'}), 400
        
        # 견적 계산
        price_info = calculate_price(
            data['printType'],
            data['bindingType'],
            safe_int_conversion(data['quantity']),
            safe_int_conversion(data['pages']),
            data.get('size', 'A4'),
            data.get('printMethod', 'single')
        )
        
        # PDF 생성
        pdf_buffer = generate_quote_pdf(data, price_info)
        
        # 파일명 생성
        customer_name = data.get('customerName', '고객')
        filename = f"견적서_{customer_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"PDF 생성 오류: {e}")
        return jsonify({'error': 'PDF 생성 중 오류가 발생했습니다.'}), 500

# 기존 라우트들 유지
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('파일이 선택되지 않았습니다.')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('파일이 선택되지 않았습니다.')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            flash('파일이 성공적으로 업로드되었습니다.')
            return redirect(url_for('my_orders'))
        else:
            flash('허용되지 않는 파일 형식입니다.')
    
    return render_template('upload.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        
        if User.query.filter_by(username=username).first():
            flash('이미 존재하는 사용자명입니다.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('이미 존재하는 이메일입니다.')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone,
            address=address
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다. 로그인해주세요.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 페이지 - 에러 핸들링 강화"""
    try:
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('사용자명과 비밀번호를 모두 입력해주세요.', 'error')
                return render_template('login.html')
            
            try:
                user = User.query.filter_by(username=username).first()
                
                if user and check_password_hash(user.password_hash, password):
                    login_user(user, remember=request.form.get('remember', False))
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('index'))
                else:
                    flash('잘못된 사용자명 또는 비밀번호입니다.', 'error')
            except Exception as e:
                print(f"⚠️ 로그인 처리 오류: {e}")
                import traceback
                traceback.print_exc()
                flash('로그인 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'error')
        
        return render_template('login.html')
    except Exception as e:
        print(f"⚠️ 로그인 페이지 오류: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>로그인 페이지 오류</h1><p>{str(e)}</p>", 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/portfolio')
def portfolio():
    """포트폴리오 페이지"""
    category = request.args.get('category', 'all')
    if category == 'all':
        portfolios = Portfolio.query.filter_by(is_active=True).order_by(Portfolio.created_at.desc()).all()
    else:
        portfolios = Portfolio.query.filter_by(category=category, is_active=True).order_by(Portfolio.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'portfolios': [{
            'id': p.id,
            'title': p.title,
            'category': p.category,
            'description': p.description,
            'image_path': p.image_path,
            'thumbnail_path': p.thumbnail_path or p.image_path,
            'created_at': p.created_at.strftime('%Y-%m-%d')
        } for p in portfolios]
    })

@app.route('/api/portfolio')
def api_portfolio():
    """포트폴리오 API (페이지네이션 지원)"""
    category = request.args.get('category', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    # 기본 쿼리
    if category == 'all':
        query = Portfolio.query.filter_by(is_active=True)
    else:
        query = Portfolio.query.filter_by(category=category, is_active=True)
    
    # 페이지네이션
    pagination = query.order_by(Portfolio.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    items = [{
        'id': p.id,
        'title': p.title,
        'category': p.category,
        'description': p.description,
        'image_path': p.image_path,
        'thumbnail_path': p.thumbnail_path or p.image_path,
        'created_at': p.created_at.strftime('%Y-%m-%d')
    } for p in pagination.items]
    
    return jsonify({
        'success': True,
        'items': items,
        'current_page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

# 관리자 포트폴리오 관리 라우트
@app.route('/admin/portfolio')
@login_required
def admin_portfolio():
    """관리자 포트폴리오 관리 페이지"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    portfolios = Portfolio.query.order_by(Portfolio.created_at.desc()).all()
    # 포트폴리오 카테고리 가져오기
    portfolio_categories = PortfolioCategory.query.filter_by(is_active=True).order_by(PortfolioCategory.display_order, PortfolioCategory.name).all()
    return render_template('admin_portfolio.html', portfolios=portfolios, portfolio_categories=portfolio_categories)

@app.route('/admin/upload_portfolio', methods=['POST'])
@login_required
def upload_portfolio():
    """포트폴리오 이미지 업로드"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 업로드할 수 있습니다.'}), 403
    
    try:
        if 'portfolio_image' not in request.files:
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['portfolio_image']
        if file.filename == '':
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not allowed_image_file(file.filename):
            return jsonify({'success': False, 'error': '지원하지 않는 이미지 형식입니다.'}), 400
        
        title = request.form.get('title', '')
        category = request.form.get('category', '기타')
        description = request.form.get('description', '')
        
        if not title:
            return jsonify({'success': False, 'error': '제목을 입력해주세요.'}), 400
        
        # 파일 저장
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['PORTFOLIO_FOLDER'], unique_filename)
        
        # 폴더가 없으면 생성
        os.makedirs(app.config['PORTFOLIO_FOLDER'], exist_ok=True)
        file.save(file_path)
        
        # 썸네일 생성
        thumbnail_filename = None
        try:
            from PIL import Image
            thumbnail_filename = f"thumb_{unique_filename}"
            thumbnail_path = os.path.join(app.config['PORTFOLIO_THUMBNAILS'], thumbnail_filename)
            
            # 썸네일 폴더가 없으면 생성
            os.makedirs(app.config['PORTFOLIO_THUMBNAILS'], exist_ok=True)
            
            img = Image.open(file_path)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            img.save(thumbnail_path, optimize=True, quality=85)
        except Exception as e:
            print(f"썸네일 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            thumbnail_filename = None
        
        # 데이터베이스에 저장
        portfolio = Portfolio(
            title=title,
            category=category,
            description=description,
            image_path=f"portfolio/{unique_filename}",
            thumbnail_path=f"portfolio/thumbnails/{thumbnail_filename}" if thumbnail_filename else None
        )
        
        db.session.add(portfolio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '포트폴리오가 성공적으로 업로드되었습니다.',
            'portfolio_id': portfolio.id
        })
        
    except Exception as e:
        print(f"포트폴리오 업로드 오류: {e}")
        return jsonify({'success': False, 'error': f'업로드 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/delete_portfolio/<int:portfolio_id>', methods=['POST'])
@login_required
def delete_portfolio(portfolio_id):
    """포트폴리오 삭제"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 삭제할 수 있습니다.'}), 403
    
    try:
        portfolio = Portfolio.query.get_or_404(portfolio_id)
        
        # 파일 삭제
        if portfolio.image_path:
            image_full_path = os.path.join('static', portfolio.image_path)
            if os.path.exists(image_full_path):
                os.remove(image_full_path)
        
        if portfolio.thumbnail_path:
            thumb_full_path = os.path.join('static', portfolio.thumbnail_path)
            if os.path.exists(thumb_full_path):
                os.remove(thumb_full_path)
        
        db.session.delete(portfolio)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '포트폴리오가 삭제되었습니다.'})
        
    except Exception as e:
        print(f"포트폴리오 삭제 오류: {e}")
        return jsonify({'success': False, 'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin')
@login_required
def admin_dashboard():
    """관리자 대시보드"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    # 통계 정보 (모든 쿼리에 오류 처리 추가)
    # 기본값을 먼저 설정하여 변수가 항상 정의되도록 함
    portfolio_count = 0
    brochure_count = 0
    order_count = 0
    question_count = 0
    unanswered_count = 0
    
    try:
        portfolio_count = Portfolio.query.filter_by(is_active=True).count()
    except Exception as e:
        print(f"⚠️ 포트폴리오 통계 조회 오류: {e}")
        portfolio_count = 0
    
    try:
        brochure_count = Brochure.query.filter_by(is_active=True).count()
    except Exception as e:
        print(f"⚠️ 브로슈어 통계 조회 오류: {e}")
        brochure_count = 0
    
    try:
        order_count = Order.query.count()
    except Exception as e:
        print(f"⚠️ 주문 통계 조회 오류: {e}")
        order_count = 0
    
    # Question 통계 (오류 처리 포함)
    try:
        # Question 테이블 존재 여부 확인
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        
        if 'question' in table_names:
            try:
                question_count = Question.query.count()
            except Exception as e:
                print(f"⚠️ 질문 개수 조회 오류: {e}")
                question_count = 0
            
            try:
                # is_answered 컬럼 존재 여부 확인
                columns = [col['name'] for col in inspector.get_columns('question')]
                if 'is_answered' in columns:
                    unanswered_count = Question.query.filter_by(is_answered=False).count()
                else:
                    unanswered_count = 0
            except Exception as e:
                print(f"⚠️ 답변 대기 질문 조회 오류: {e}")
                unanswered_count = 0
        else:
            print("⚠️ question 테이블이 존재하지 않습니다.")
            question_count = 0
            unanswered_count = 0
    except Exception as e:
        print(f"⚠️ 질문 통계 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        # Question 테이블이 없거나 오류 발생 시 기본값 사용
        question_count = 0
        unanswered_count = 0
    
    # 최종 확인: 모든 변수가 정의되었는지 확인 (안전장치)
    if 'unanswered_count' not in locals() or unanswered_count is None:
        unanswered_count = 0
    if 'question_count' not in locals() or question_count is None:
        question_count = 0
    
    # 템플릿에 전달할 변수 딕셔너리 생성 (명시적으로)
    template_vars = {
        'portfolio_count': portfolio_count,
        'brochure_count': brochure_count,
        'order_count': order_count,
        'question_count': question_count,
        'unanswered_count': unanswered_count
    }
    
    return render_template('admin_dashboard.html', **template_vars)

@app.route('/admin/files')
@login_required
def admin_files():
    """관리자 파일 관리 페이지"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    # 업로드된 파일 목록 가져오기
    upload_files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                upload_files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return render_template('admin_files.html', files=upload_files)

@app.route('/admin/delete_file', methods=['POST'])
@login_required
def delete_file():
    """파일 삭제"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 삭제할 수 있습니다.'}), 403
    
    try:
        filename = request.json.get('filename')
        if not filename:
            return jsonify({'success': False, 'error': '파일명이 필요합니다.'}), 400
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'message': '파일이 삭제되었습니다.'})
        else:
            return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다.'}), 404
            
    except Exception as e:
        print(f"파일 삭제 오류: {e}")
        return jsonify({'success': False, 'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500

# 리플렛/브로슈어 관리 라우트
@app.route('/admin/brochures')
@login_required
def admin_brochures():
    """관리자 리플렛/브로슈어 관리 페이지"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    brochures = Brochure.query.order_by(Brochure.created_at.desc()).all()
    return render_template('admin_brochures.html', brochures=brochures)

@app.route('/admin/upload_brochure', methods=['POST'])
@login_required
def upload_brochure():
    """리플렛/브로슈어 파일 업로드"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 업로드할 수 있습니다.'}), 403
    
    try:
        if 'brochure_file' not in request.files:
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['brochure_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'}), 400
        
        # 파일 확장자 확인
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in app.config['ALLOWED_BROCHURE_EXTENSIONS']:
            allowed_formats = ', '.join(sorted(app.config['ALLOWED_BROCHURE_EXTENSIONS'])).upper()
            return jsonify({'success': False, 'error': f'지원하지 않는 파일 형식입니다. 지원 형식: {allowed_formats}'}), 400
        
        title = request.form.get('title', '')
        category = request.form.get('category', '리플렛')
        description = request.form.get('description', '')
        
        if not title:
            return jsonify({'success': False, 'error': '제목을 입력해주세요.'}), 400
        
        # 파일 저장
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['BROCHURE_FOLDER'], unique_filename)
        
        # 폴더가 없으면 생성
        os.makedirs(app.config['BROCHURE_FOLDER'], exist_ok=True)
        file.save(file_path)
        
        # 파일 크기
        file_size = os.path.getsize(file_path)
        
        # 썸네일 생성 (이미지인 경우)
        thumbnail_path = None
        if file_ext in app.config['ALLOWED_IMAGE_EXTENSIONS']:
            try:
                from PIL import Image
                thumbnail_filename = f"thumb_{unique_filename}"
                thumbnail_path_full = os.path.join(app.config['BROCHURE_THUMBNAILS'], thumbnail_filename)
                
                # 썸네일 폴더가 없으면 생성
                os.makedirs(app.config['BROCHURE_THUMBNAILS'], exist_ok=True)
                
                img = Image.open(file_path)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                img.save(thumbnail_path_full, optimize=True, quality=85)
                thumbnail_path = f"brochures/thumbnails/{thumbnail_filename}"
            except Exception as e:
                print(f"썸네일 생성 오류: {e}")
                import traceback
                traceback.print_exc()
        
        # 데이터베이스에 저장
        brochure = Brochure(
            title=title,
            category=category,
            description=description,
            file_path=f"brochures/{unique_filename}",
            thumbnail_path=thumbnail_path,
            file_type=file_ext,
            file_size=file_size
        )
        
        db.session.add(brochure)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '리플렛/브로슈어가 성공적으로 업로드되었습니다.',
            'brochure_id': brochure.id
        })
        
    except Exception as e:
        print(f"리플렛 업로드 오류: {e}")
        return jsonify({'success': False, 'error': f'업로드 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/delete_brochure/<int:brochure_id>', methods=['POST'])
@login_required
def delete_brochure(brochure_id):
    """리플렛/브로슈어 삭제"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 삭제할 수 있습니다.'}), 403
    
    try:
        brochure = Brochure.query.get_or_404(brochure_id)
        
        # 파일 삭제
        if brochure.file_path:
            file_full_path = os.path.join('static', brochure.file_path)
            if os.path.exists(file_full_path):
                os.remove(file_full_path)
        
        if brochure.thumbnail_path:
            thumb_full_path = os.path.join('static', brochure.thumbnail_path)
            if os.path.exists(thumb_full_path):
                os.remove(thumb_full_path)
        
        db.session.delete(brochure)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '리플렛/브로슈어가 삭제되었습니다.'})
        
    except Exception as e:
        print(f"리플렛 삭제 오류: {e}")
        return jsonify({'success': False, 'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500

# 서비스 카테고리 관리 라우트
@app.route('/admin/service_categories')
@login_required
def admin_service_categories():
    """서비스 카테고리 관리 페이지"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    categories = ServiceCategory.query.order_by(ServiceCategory.display_order, ServiceCategory.name).all()
    return render_template('admin_service_categories.html', categories=categories)

@app.route('/admin/add_service_category', methods=['POST'])
@login_required
def add_service_category():
    """서비스 카테고리 추가"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 추가할 수 있습니다.'}), 403
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        display_name = data.get('display_name', '').strip()
        description = data.get('description', '').strip()
        icon = data.get('icon', 'fas fa-book').strip()
        color = data.get('color', 'primary').strip()
        display_order = int(data.get('display_order', 0))
        
        if not name or not display_name:
            return jsonify({'success': False, 'error': '이름과 표시 이름을 입력해주세요.'}), 400
        
        # 중복 확인
        if ServiceCategory.query.filter_by(name=name).first():
            return jsonify({'success': False, 'error': '이미 존재하는 서비스 이름입니다.'}), 400
        
        category = ServiceCategory(
            name=name,
            display_name=display_name,
            description=description,
            icon=icon,
            color=color,
            display_order=display_order,
            is_active=True
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '서비스 카테고리가 추가되었습니다.',
            'category_id': category.id
        })
        
    except Exception as e:
        print(f"서비스 카테고리 추가 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'추가 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/update_service_category/<int:category_id>', methods=['POST'])
@login_required
def update_service_category(category_id):
    """서비스 카테고리 수정"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 수정할 수 있습니다.'}), 403
    
    try:
        category = ServiceCategory.query.get_or_404(category_id)
        
        # 파일 업로드 처리
        if 'service_image' in request.files:
            file = request.files['service_image']
            if file.filename != '':
                if allowed_image_file(file.filename):
                    # 기존 이미지 삭제
                    if category.image_path:
                        old_path = os.path.join('static', category.image_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    # 새 이미지 저장
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['SERVICE_IMAGE_FOLDER'], unique_filename)
                    os.makedirs(app.config['SERVICE_IMAGE_FOLDER'], exist_ok=True)
                    file.save(file_path)
                    category.image_path = f"service_images/{unique_filename}"
        
        # JSON 데이터 처리 (일반 수정)
        if request.is_json:
            data = request.get_json()
            if 'display_name' in data:
                category.display_name = data['display_name'].strip()
            if 'description' in data:
                category.description = data['description'].strip()
            if 'icon' in data:
                category.icon = data['icon'].strip()
            if 'color' in data:
                category.color = data['color'].strip()
            if 'display_order' in data:
                category.display_order = int(data['display_order'])
            if 'is_active' in data:
                category.is_active = bool(data['is_active'])
        else:
            # 폼 데이터 처리
            if 'display_name' in request.form:
                category.display_name = request.form['display_name'].strip()
            if 'description' in request.form:
                category.description = request.form['description'].strip()
            if 'icon' in request.form:
                category.icon = request.form['icon'].strip()
            if 'color' in request.form:
                category.color = request.form['color'].strip()
            if 'display_order' in request.form:
                category.display_order = int(request.form.get('display_order', 0))
            if 'is_active' in request.form:
                category.is_active = bool(request.form.get('is_active'))
        
        category.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '서비스 카테고리가 수정되었습니다.'
        })
        
    except Exception as e:
        print(f"서비스 카테고리 수정 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'수정 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/delete_service_category/<int:category_id>', methods=['POST'])
@login_required
def delete_service_category(category_id):
    """서비스 카테고리 삭제"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 삭제할 수 있습니다.'}), 403
    
    try:
        category = ServiceCategory.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '서비스 카테고리가 삭제되었습니다.'})
        
    except Exception as e:
        print(f"서비스 카테고리 삭제 오류: {e}")
        return jsonify({'success': False, 'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/service_categories')
def get_service_categories():
    """활성화된 서비스 카테고리 목록 API"""
    categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.display_order, ServiceCategory.name).all()
    return jsonify({
        'success': True,
        'categories': [{
            'id': c.id,
            'name': c.name,
            'display_name': c.display_name,
            'description': c.description,
            'icon': c.icon,
            'color': c.color
        } for c in categories]
    })

# 포트폴리오 카테고리 관리 라우트
@app.route('/admin/board')
@login_required
def admin_board():
    """관리자 게시판 관리 페이지"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    try:
        # 카테고리 목록
        categories = BoardCategory.query.order_by(BoardCategory.display_order, BoardCategory.name).all()
        
        # 전체 게시글 수
        total_posts = BoardPost.query.count()
        
        # 카테고리별 게시글 수
        category_counts = {}
        for category in categories:
            category_counts[category.id] = BoardPost.query.filter_by(category_id=category.id).count()
        
        return render_template('admin_board.html',
                             categories=categories,
                             total_posts=total_posts,
                             category_counts=category_counts)
    except Exception as e:
        print(f"⚠️ 게시판 관리 페이지 오류: {e}")
        import traceback
        traceback.print_exc()
        return render_template('admin_board.html',
                             categories=[],
                             total_posts=0,
                             category_counts={})

@app.route('/admin/board/category', methods=['POST'])
@login_required
def admin_board_category():
    """게시판 카테고리 추가/수정"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
    
    try:
        action = request.json.get('action')  # 'add' or 'update'
        category_id = request.json.get('category_id')
        name = request.json.get('name', '').strip()
        description = request.json.get('description', '').strip()
        display_order = request.json.get('display_order', 0)
        
        if not name:
            return jsonify({'success': False, 'error': '카테고리 이름을 입력해주세요.'}), 400
        
        if action == 'add':
            # 중복 확인
            if BoardCategory.query.filter_by(name=name).first():
                return jsonify({'success': False, 'error': '이미 존재하는 카테고리 이름입니다.'}), 400
            
            category = BoardCategory(
                name=name,
                description=description,
                display_order=display_order
            )
            db.session.add(category)
        elif action == 'update':
            category = BoardCategory.query.get_or_404(category_id)
            # 이름 중복 확인 (자기 자신 제외)
            existing = BoardCategory.query.filter_by(name=name).first()
            if existing and existing.id != category_id:
                return jsonify({'success': False, 'error': '이미 존재하는 카테고리 이름입니다.'}), 400
            
            category.name = name
            category.description = description
            category.display_order = display_order
        
        db.session.commit()
        return jsonify({'success': True, 'message': '카테고리가 저장되었습니다.'})
    except Exception as e:
        db.session.rollback()
        print(f"게시판 카테고리 저장 오류: {e}")
        return jsonify({'success': False, 'error': f'저장 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/board/category/<int:category_id>', methods=['DELETE'])
@login_required
def delete_board_category(category_id):
    """게시판 카테고리 삭제"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 삭제할 수 있습니다.'}), 403
    
    try:
        category = BoardCategory.query.get_or_404(category_id)
        
        # 해당 카테고리의 게시글 수 확인
        posts_count = BoardPost.query.filter_by(category_id=category_id).count()
        if posts_count > 0:
            return jsonify({
                'success': False,
                'error': f'이 카테고리에 게시글이 {posts_count}개 있습니다. 먼저 게시글을 삭제하거나 다른 카테고리로 이동해주세요.'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True, 'message': '카테고리가 삭제되었습니다.'})
    except Exception as e:
        db.session.rollback()
        print(f"게시판 카테고리 삭제 오류: {e}")
        return jsonify({'success': False, 'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/admin/board/posts', methods=['GET'])
@login_required
def get_admin_board_posts():
    """관리자용 게시글 목록 API"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
    
    try:
        category_id = request.args.get('category_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = BoardPost.query
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        posts = query.order_by(BoardPost.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        posts_data = []
        for post in posts.items:
            posts_data.append({
                'id': post.id,
                'category_name': post.category.name if post.category else '',
                'title': post.title,
                'author_name': post.author_name,
                'view_count': post.view_count,
                'is_notice': post.is_notice,
                'is_pinned': post.is_pinned,
                'is_active': post.is_active,
                'created_at': post.created_at.strftime('%Y-%m-%d %H:%M') if post.created_at else '',
                'has_file': bool(post.file_path)
            })
        
        return jsonify({
            'success': True,
            'posts': posts_data,
            'total': posts.total,
            'pages': posts.pages,
            'current_page': page,
            'has_next': posts.has_next,
            'has_prev': posts.has_prev
        })
    except Exception as e:
        print(f"⚠️ 게시글 목록 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '게시글 목록을 불러오는 중 오류가 발생했습니다.'}), 500

@app.route('/api/admin/board/post/<int:post_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_board_post(post_id):
    """게시글 수정/삭제"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
    
    try:
        post = BoardPost.query.get_or_404(post_id)
        
        if request.method == 'DELETE':
            # 파일 삭제
            if post.file_path:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], post.file_path)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"⚠️ 파일 삭제 실패: {e}")
            
            db.session.delete(post)
            db.session.commit()
            return jsonify({'success': True, 'message': '게시글이 삭제되었습니다.'})
        
        elif request.method == 'PUT':
            # 게시글 수정
            data = request.json
            post.title = data.get('title', post.title)
            post.content = data.get('content', post.content)
            post.is_notice = data.get('is_notice', post.is_notice)
            post.is_pinned = data.get('is_pinned', post.is_pinned)
            post.is_active = data.get('is_active', post.is_active)
            post.updated_at = datetime.utcnow()
            
            db.session.commit()
            return jsonify({'success': True, 'message': '게시글이 수정되었습니다.'})
    except Exception as e:
        db.session.rollback()
        print(f"게시글 관리 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/portfolio_categories')
@login_required
def admin_portfolio_categories():
    """포트폴리오 카테고리 관리 페이지"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    categories = PortfolioCategory.query.order_by(PortfolioCategory.display_order, PortfolioCategory.name).all()
    return render_template('admin_portfolio_categories.html', categories=categories)

@app.route('/admin/add_portfolio_category', methods=['POST'])
@login_required
def add_portfolio_category():
    """포트폴리오 카테고리 추가"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 추가할 수 있습니다.'}), 403
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        display_order = int(data.get('display_order', 0))
        
        if not name:
            return jsonify({'success': False, 'error': '카테고리 이름을 입력해주세요.'}), 400
        
        # 중복 확인
        if PortfolioCategory.query.filter_by(name=name).first():
            return jsonify({'success': False, 'error': '이미 존재하는 카테고리 이름입니다.'}), 400
        
        category = PortfolioCategory(
            name=name,
            display_order=display_order,
            is_active=True
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '포트폴리오 카테고리가 추가되었습니다.',
            'category_id': category.id
        })
        
    except Exception as e:
        print(f"포트폴리오 카테고리 추가 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'추가 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/update_portfolio_category/<int:category_id>', methods=['POST'])
@login_required
def update_portfolio_category(category_id):
    """포트폴리오 카테고리 수정"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 수정할 수 있습니다.'}), 403
    
    try:
        category = PortfolioCategory.query.get_or_404(category_id)
        
        data = request.get_json()
        
        if 'name' in data:
            new_name = data['name'].strip()
            if new_name:
                # 중복 확인 (자기 자신 제외)
                existing = PortfolioCategory.query.filter_by(name=new_name).first()
                if existing and existing.id != category_id:
                    return jsonify({'success': False, 'error': '이미 존재하는 카테고리 이름입니다.'}), 400
                category.name = new_name
        
        if 'display_order' in data:
            category.display_order = int(data['display_order'])
        
        if 'is_active' in data:
            category.is_active = bool(data['is_active'])
        
        category.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '포트폴리오 카테고리가 수정되었습니다.'
        })
        
    except Exception as e:
        print(f"포트폴리오 카테고리 수정 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'수정 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/delete_portfolio_category/<int:category_id>', methods=['POST'])
@login_required
def delete_portfolio_category(category_id):
    """포트폴리오 카테고리 삭제"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 삭제할 수 있습니다.'}), 403
    
    try:
        category = PortfolioCategory.query.get_or_404(category_id)
        
        # 해당 카테고리를 사용하는 포트폴리오가 있는지 확인
        portfolios_count = Portfolio.query.filter_by(category=category.name).count()
        if portfolios_count > 0:
            return jsonify({
                'success': False, 
                'error': f'이 카테고리를 사용하는 포트폴리오가 {portfolios_count}개 있습니다. 먼저 포트폴리오의 카테고리를 변경해주세요.'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '포트폴리오 카테고리가 삭제되었습니다.'})
        
    except Exception as e:
        print(f"포트폴리오 카테고리 삭제 오류: {e}")
        return jsonify({'success': False, 'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500

def register_korean_fonts():
    """한글 폰트 등록"""
    try:
        # Windows 시스템 폰트 경로
        font_paths = [
            'C:/Windows/Fonts/malgun.ttf',  # 맑은 고딕
            'C:/Windows/Fonts/malgunbd.ttf',  # 맑은 고딕 Bold
            'C:/Windows/Fonts/gulim.ttc',  # 굴림
            'C:/Windows/Fonts/batang.ttc',  # 바탕
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    if font_path.endswith('.ttf'):
                        pdfmetrics.registerFont(TTFont('Malgun', font_path))
                        pdfmetrics.registerFont(TTFont('MalgunBold', font_path))
                    elif font_path.endswith('.ttc'):
                        # TTC 파일의 경우 첫 번째 폰트만 등록
                        pdfmetrics.registerFont(TTFont('Malgun', font_path, subfontIndex=0))
                    print(f"✅ 폰트 등록 성공: {font_path}")
                    break
                except Exception as e:
                    print(f"⚠️ 폰트 등록 실패: {font_path} - {e}")
                    continue
        
        # 기본 폰트 설정
        return 'Malgun'
        
    except Exception as e:
        print(f"⚠️ 폰트 등록 중 오류: {e}")
        return 'Helvetica'  # 기본 폰트 사용

def create_company_seal():
    """회사 도장 생성 (개선된 버전)"""
    try:
        # 도장 크기 설정 (더 크게)
        seal_size = 30*mm
        
        # 도장 그리기
        drawing = Drawing(seal_size, seal_size)
        
        # 외곽 원 (빨간색, 두꺼운 테두리)
        outer_circle = Circle(seal_size/2, seal_size/2, seal_size/2 - 1*mm, 
                             strokeColor=colors.red, fillColor=None, strokeWidth=3)
        drawing.add(outer_circle)
        
        # 내부 원 (빨간색, 얇은 테두리)
        inner_circle = Circle(seal_size/2, seal_size/2, seal_size/2 - 3*mm, 
                             strokeColor=colors.red, fillColor=None, strokeWidth=1)
        drawing.add(inner_circle)
        
        # 회사명 텍스트 (중앙, 더 큰 폰트)
        company_text = String(seal_size/2, seal_size/2 + 2*mm, '온누리인쇄나라', 
                             textAnchor='middle', fontSize=10, fillColor=colors.red)
        drawing.add(company_text)
        
        # 대표자명 텍스트 (하단, 더 큰 폰트)
        ceo_text = String(seal_size/2, seal_size/2 - 2*mm, '류도현', 
                         textAnchor='middle', fontSize=8, fillColor=colors.red)
        drawing.add(ceo_text)
        
        print("✅ 도장 생성 완료")
        return drawing
        
    except Exception as e:
        print(f"⚠️ 도장 생성 중 오류: {e}")
        return None

def generate_quote_pdf(data, price_info):
    """견적서 PDF 생성 (이미지 양식과 동일하게)"""
    try:
        # PDF 버퍼 생성
        buffer = io.BytesIO()
        
        # PDF 문서 생성 (여백 최소화)
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=15*mm, leftMargin=15*mm,
                              topMargin=15*mm, bottomMargin=15*mm)
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        
        # 한글 폰트 등록
        font_name = register_korean_fonts()
        
        # 커스텀 스타일 정의
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=24,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=15,
            letterSpacing=0.2
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=4
        )
        
        # 스토리 리스트 생성
        story = []
        
        # 제목 (이미지와 동일하게)
        story.append(Paragraph("견&nbsp;&nbsp;&nbsp;적&nbsp;&nbsp;&nbsp;서", title_style))
        story.append(Spacer(1, 15))
        
        # 메인 정보 섹션 (좌우 배치) - 미리보기와 동일하게
        # 왼쪽: 수신자 정보 (일련번호, 참조, 전화번호 삭제)
        from datetime import datetime
        today = datetime.now()
        left_data = [
            ['수신', f"{data.get('customerName', '1')}"],
            ['견적일자', f"{today.year}년 {today.month}월 {today.day}일"]
        ]
        
        left_table = Table(left_data, colWidths=[25*mm, 60*mm])
        left_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f6f6f6')),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        # 오른쪽: 회사 정보 (미리보기와 정확히 동일)
        right_data = [
            ['상호', '온누리인쇄나라'],
            ['사업자번호', '491-20-00640'],
            ['대표자', '류도현'],
            ['주소', '서울 금천구 가산디지털1로 142 가산더스카이밸리1차 8층 816호'],
            ['업태', '제조, 소매, 서비스업'],
            ['종목', '경인쇄, 문구, 출력, 복사, 제본'],
            ['사업자계좌번호', '신한 110-493-223413'],
            ['전화번호', '02-6338-7123']
        ]
        
        right_table = Table(right_data, colWidths=[25*mm, 60*mm])
        right_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f6f6f6')),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # 주소와 종목은 왼쪽 정렬로 변경
            ('ALIGN', (1, 3), (1, 3), 'LEFT'),  # 주소
            ('ALIGN', (1, 5), (1, 5), 'LEFT'),  # 종목
        ]))
        
        # 좌우 테이블을 하나의 테이블로 결합
        combined_data = [
            [left_table, right_table]
        ]
        
        combined_table = Table(combined_data, colWidths=[85*mm, 85*mm])
        combined_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0)
        ]))
        
        story.append(combined_table)
        story.append(Spacer(1, 10))
        
        # 설명 문구
        story.append(Paragraph("아래와 같이 견적 합니다", normal_style))
        story.append(Spacer(1, 10))
        
        # 합계금액 섹션 (미리보기와 동일하게 설명 문구 아래에 배치)
        total_amount = price_info.get("total_price", 2220)  # 실제 계산된 금액 사용
        total_amount_korean = convert_number_to_korean(int(total_amount))
        
        total_data = [
            ['합계금액', f'₩ {total_amount:,}', '일금', f'({total_amount_korean}원)']
        ]
        
        total_table = Table(total_data, colWidths=[25*mm, 35*mm, 25*mm, 55*mm])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 14),  # 폰트 크기 증가 (10 → 14)
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 10),  # 상하 패딩 증가 (8 → 10)
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # 금액 부분 더 강조
            ('FONTSIZE', (1, 0), (1, 0), 16),  # 금액 폰트 더 크게
            ('FONTSIZE', (3, 0), (3, 0), 12),  # 한글 금액도 크게
        ]))
        
        story.append(total_table)
        story.append(Spacer(1, 10))
        
        # 상품 상세 테이블 (미리보기와 정확히 동일)
        item_data = [
            ['상품명', '단가적용구간', '규격', '수량', '단가', '공급가액', '세액', '비고'],
            ['흑백 단면 링제본', f"{data.get('pages', 10)}페이지", 'A4', f"{data.get('quantity', 1)}", f'₩{price_info.get("unit_price", 2220):,}', f'₩{int(price_info.get("total_price", 2220)/1.1):,}', f'₩{int(price_info.get("total_price", 2220)*0.1/1.1):,}', '']
        ]
        
        # 빈 행 3개 추가
        for _ in range(3):
            item_data.append(['', '', '', '', '', '', '', ''])
        
        item_table = Table(item_data, colWidths=[35*mm, 20*mm, 15*mm, 15*mm, 20*mm, 25*mm, 20*mm, 15*mm])
        item_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # 상품명은 왼쪽 정렬
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ]))
        
        story.append(item_table)
        
        # 하단 여백
        story.append(Spacer(1, 30))
        
        # PDF 생성
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"PDF 생성 오류: {e}")
        return None
    # 한글 폰트 등록
    font_name = register_korean_fonts()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    
    # 스타일 정의
    styles = getSampleStyleSheet()
    
    # 제목 스타일 (한글 폰트 적용)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        fontName=font_name,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # 일반 텍스트 스타일 (한글 폰트 적용)
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name,
        alignment=TA_LEFT
    )
    
    # 테이블 스타일 (한글 폰트 적용)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
    ])
    
    # 도장 먼저 생성
    company_seal = create_company_seal()
    
    # 문서 내용 구성
    story = []
    
    # 제목
    story.append(Paragraph("견적서", title_style))
    story.append(Spacer(1, 10))
    
    # 수신자 정보 테이블 (제공된 양식에 맞게 수정)
    recipient_data = [
        ['일련번호', '', '수신', data.get('customerName', '고객님') + ' 귀하'],
        ['참조', '', '전화번호', data.get('phone', '')],
        ['견적일자', '2025년 08월 11일', '', '']
    ]
    
    recipient_table = Table(recipient_data, colWidths=[30*mm, 40*mm, 20*mm, 60*mm])
    recipient_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(recipient_table)
    story.append(Spacer(1, 10))
    
    # "아래와 같이 견적합니다" 문구
    story.append(Paragraph("아래와 같이 견적합니다.", normal_style))
    story.append(Spacer(1, 10))
    
    # 공급자 정보 테이블 (제공된 양식에 맞게 수정)
    supplier_data = [
        ['공급자'],
        ['상호', '온누리인쇄나라'],
        ['사업자번호', '491-20-00640'],
        ['대표자', '류도현'],
        ['주소', '서울 금천구 가산디지털1로 142 가산더스카이밸리1차 8층 816호'],
        ['업태', '제조, 소매, 서비스업'],
        ['종목', '경인쇄, 문구, 출력, 복사, 제본'],
        ['사업자계좌번호', '신한 110-493-223413'],
        ['전화번호', '02-6338-7123']
    ]
    
    supplier_table = Table(supplier_data, colWidths=[30*mm, 120*mm])
    supplier_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
    ]))
    
    story.append(supplier_table)
    story.append(Spacer(1, 20))
    
    # 합계금액 (제공된 양식에 맞게 수정)
    total_amount = price_info['total_price']
    total_amount_korean = convert_number_to_korean(int(total_amount))
    
    total_data = [
        ['합계금액', f'일금 {total_amount_korean}원정', f'(W {total_amount:,.0f})']
    ]
    
    total_table = Table(total_data, colWidths=[30*mm, 80*mm, 40*mm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 20))
    
    # 상품명 및 상세 정보
    print_type_map = {
        'black_white': '흑백',
        'laser_color': '레이저칼라',
        'ink_color': '잉크칼라'
    }
    
    binding_type_map = {
        'ring': '링제본',
        'perfect': '무선제본',
        'saddle': '중철제본',
        'folding': '접지제본'
    }
    
    print_method_map = {
        'single': '단면',
        'double': '양면'
    }
    
    product_name = f"A4 {print_type_map.get(data.get('printType', ''), '')} {print_method_map.get(data.get('printMethod', ''), '')} {binding_type_map.get(data.get('bindingType', ''), '')}"
    
    # 상품 상세 테이블 (제공된 양식에 맞게 수정)
    item_data = [
        ['상품명', '단가적용구간', '규격', '수량', '단가', '공급가액', '세액', '비고'],
        [product_name, '', '', str(data.get('quantity', '')), 
         f"{price_info['unit_price']:,.0f}", 
         f"{price_info['total_price']:,.0f}", 
         f"{price_info['total_price'] * 0.1:,.0f}", '']
    ]
    
    item_table = Table(item_data, colWidths=[40*mm, 25*mm, 20*mm, 15*mm, 20*mm, 25*mm, 20*mm, 25*mm])
    item_table.setStyle(table_style)
    
    story.append(item_table)
    
    # 서명 및 도장 영역 추가 (도장을 먼저 그리고 그 위에 서명 정보 올리기)
    story.append(Spacer(1, 30))
    
    # 도장과 서명을 함께 배치하는 테이블 생성
    if company_seal:
        # 도장과 서명 정보를 한 테이블에 배치
        signature_seal_data = [
            ['', '', '', company_seal],
            ['', '', '', ''],
            ['', '온누리인쇄나라', '', ''],
            ['', '대표: 류도현', '', ''],
            ['', '2025년 08월 11일', '', '']
        ]
        
        signature_seal_table = Table(signature_seal_data, colWidths=[40*mm, 50*mm, 20*mm, 40*mm])
        signature_seal_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, 0), 'RIGHT'),  # 도장 오른쪽 정렬
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (1, 2), (1, 2), 1, colors.black),  # 회사명 아래 선
            ('LINEBELOW', (1, 3), (1, 3), 1, colors.black),  # 대표명 아래 선
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0)
        ]))
        
        story.append(signature_seal_table)
    else:
        # 도장이 없는 경우 기본 서명 테이블
        signature_data = [
            ['', '', ''],
            ['', '', ''],
            ['', '온누리인쇄나라', ''],
            ['', '대표: 류도현', ''],
            ['', datetime.now().strftime('%Y년 %m월 %d일'), '']
        ]
        
        signature_table = Table(signature_data, colWidths=[60*mm, 60*mm, 30*mm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (1, 2), (1, 2), 1, colors.black),  # 회사명 아래 선
            ('LINEBELOW', (1, 3), (1, 3), 1, colors.black),  # 대표명 아래 선
        ]))
        
        story.append(signature_table)
    
    # PDF 생성
    doc.build(story)
    buffer.seek(0)
    return buffer

def safe_int_conversion(value):
    """안전한 정수 변환 함수"""
    try:
        if value is None or value == '':
            return 0
        
        if isinstance(value, str):
            # 빈 문자열이나 공백 처리
            value = value.strip()
            if not value:
                return 0
            
            # 소수점이 있는 경우 처리
            if '.' in value:
                return int(float(value))
            else:
                return int(value)
        elif isinstance(value, (int, float)):
            return int(value)
        else:
            return int(str(value))
    except (ValueError, TypeError):
        print(f"정수 변환 오류: {value}")
        return 0

def convert_number_to_korean(number):
    """숫자를 한글로 변환 (개선된 버전)"""
    if number == 0:
        return '영'
    
    # 한글 숫자 매핑
    units = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
    tens = ['', '십', '백', '천']
    big_units = ['', '만', '억', '조']
    
    # 숫자를 문자열로 변환하고 뒤집기
    num_str = str(number)[::-1]
    result = []
    
    for i, digit in enumerate(num_str):
        if digit == '0':
            continue
            
        # 큰 단위 (만, 억, 조)
        if i % 4 == 0 and i > 0:
            big_unit_idx = i // 4
            if big_unit_idx < len(big_units):
                result.append(big_units[big_unit_idx])
        
        # 작은 단위 (십, 백, 천)
        small_unit_idx = i % 4
        if small_unit_idx > 0 and digit != '1':
            result.append(tens[small_unit_idx])
        elif small_unit_idx > 0 and digit == '1':
            result.append(tens[small_unit_idx])
        
        # 숫자
        if digit != '1' or small_unit_idx == 0:
            result.append(units[int(digit)])
    
    # 결과 뒤집기
    result.reverse()
    return ''.join(result)

# Q&A 문의 API 엔드포인트
def update_question_schema():
    """Question 테이블 스키마를 확실하게 업데이트하는 함수 (강제 수정 버전)"""
    import sqlite3
    from sqlalchemy import inspect, text
    
    # 방법 1: SQLite 직접 연결로 강제 수정 시도
    # Flask가 설정한 데이터베이스 경로 사용 (일관성 유지)
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    # sqlite:/// 경로에서 실제 파일 경로 추출
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '').replace('/', os.sep)
        # 절대 경로인 경우 (C:로 시작)
        if len(db_path) > 1 and db_path[1] == ':':
            pass  # 이미 절대 경로
        else:
            # 상대 경로인 경우 절대 경로로 변환
            db_path = os.path.abspath(db_path)
    else:
        # 기본 경로 시도
        possible_paths = [
            os.path.join(script_dir, 'onnuri_print_enhanced.db'),
            os.path.join(script_dir, 'instance', 'onnuri_print_enhanced.db'),
        ]
        db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
        if not db_path:
            instance_dir = os.path.join(script_dir, 'instance')
            os.makedirs(instance_dir, exist_ok=True)
            db_path = os.path.join(instance_dir, 'onnuri_print_enhanced.db')
    
    print(f"📁 [스키마업데이트] 데이터베이스 경로: {db_path}")
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # question 테이블 존재 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question'")
            if cursor.fetchone():
                # 현재 컬럼 확인
                cursor.execute("PRAGMA table_info(question)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # 필요한 컬럼 추가
                if 'file_path' not in columns:
                    try:
                        cursor.execute("ALTER TABLE question ADD COLUMN file_path VARCHAR(500)")
                        conn.commit()
                        print("✅ [직접수정] file_path 컬럼 추가 완료")
                    except sqlite3.OperationalError as e:
                        if 'duplicate' not in str(e).lower():
                            print(f"⚠️ [직접수정] file_path 추가 실패: {e}")
                
                if 'is_public' not in columns:
                    try:
                        cursor.execute("ALTER TABLE question ADD COLUMN is_public INTEGER DEFAULT 1")
                        conn.commit()
                        print("✅ [직접수정] is_public 컬럼 추가 완료")
                        cursor.execute("UPDATE question SET is_public = 1 WHERE is_public IS NULL")
                        conn.commit()
                    except sqlite3.OperationalError as e:
                        if 'duplicate' not in str(e).lower():
                            print(f"⚠️ [직접수정] is_public 추가 실패: {e}")
                
                if 'password_hash' not in columns:
                    try:
                        cursor.execute("ALTER TABLE question ADD COLUMN password_hash VARCHAR(200)")
                        conn.commit()
                        print("✅ [직접수정] password_hash 컬럼 추가 완료")
                    except sqlite3.OperationalError as e:
                        if 'duplicate' not in str(e).lower():
                            print(f"⚠️ [직접수정] password_hash 추가 실패: {e}")
            
            conn.close()
        except Exception as direct_error:
            print(f"⚠️ 직접 수정 실패, SQLAlchemy 방식으로 시도: {direct_error}")
    
    # 방법 2: SQLAlchemy를 통한 수정 (기존 방식)
    try:
        inspector = inspect(db.engine)
        
        # question 테이블이 없으면 생성
        if 'question' not in inspector.get_table_names():
            print("📝 question 테이블이 없습니다. 생성 중...")
            db.create_all()
            print("✅ question 테이블 생성 완료")
            return True
        
        # 컬럼 목록 가져오기
        try:
            columns = [col['name'] for col in inspector.get_columns('question')]
            print(f"📋 question 테이블 현재 컬럼: {columns}")
        except Exception as col_error:
            print(f"⚠️ question 테이블 컬럼 조회 실패: {col_error}")
            columns = []
        
        updated = False
        
        # file_path 컬럼 추가
        if 'file_path' not in columns:
            print("📝 file_path 컬럼 추가 중...")
            try:
                db.session.execute(text('ALTER TABLE question ADD COLUMN file_path VARCHAR(500)'))
                db.session.commit()
                print("✅ file_path 컬럼 추가 완료")
                columns.append('file_path')
                updated = True
            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate column' in error_msg or 'already exists' in error_msg:
                    print("ℹ️ file_path 컬럼이 이미 존재합니다.")
                    columns.append('file_path')
                else:
                    print(f"⚠️ file_path 컬럼 추가 실패: {e}")
                    db.session.rollback()
        
        # is_public 컬럼 추가
        if 'is_public' not in columns:
            print("📝 is_public 컬럼 추가 중...")
            try:
                db.session.execute(text('ALTER TABLE question ADD COLUMN is_public INTEGER DEFAULT 1'))
                db.session.commit()
                print("✅ is_public 컬럼 추가 완료")
                columns.append('is_public')
                updated = True
                # 기존 데이터 업데이트
                try:
                    db.session.execute(text('UPDATE question SET is_public = 1 WHERE is_public IS NULL'))
                    db.session.commit()
                except:
                    pass
            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate column' in error_msg or 'already exists' in error_msg:
                    print("ℹ️ is_public 컬럼이 이미 존재합니다.")
                    columns.append('is_public')
                else:
                    print(f"⚠️ is_public 컬럼 추가 실패: {e}")
                    db.session.rollback()
        
        # password_hash 컬럼 추가
        if 'password_hash' not in columns:
            print("📝 password_hash 컬럼 추가 중...")
            try:
                db.session.execute(text('ALTER TABLE question ADD COLUMN password_hash VARCHAR(200)'))
                db.session.commit()
                print("✅ password_hash 컬럼 추가 완료")
                columns.append('password_hash')
                updated = True
            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate column' in error_msg or 'already exists' in error_msg:
                    print("ℹ️ password_hash 컬럼이 이미 존재합니다.")
                    columns.append('password_hash')
                else:
                    print(f"⚠️ password_hash 컬럼 추가 실패: {e}")
                    db.session.rollback()
        
        if updated:
            print("✅ Question 테이블 스키마 업데이트 완료")
        else:
            print("ℹ️ Question 테이블 스키마가 이미 최신 상태입니다.")
        
        return True
    except Exception as e:
        print(f"⚠️ 스키마 업데이트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        try:
            db.session.rollback()
        except:
            pass
        return False

@app.route('/api/question', methods=['POST'])
def submit_question():
    """익명 질문 제출 (파일 업로드 지원)"""
    from sqlalchemy import text
    try:
        # 데이터베이스 스키마를 확실하게 업데이트
        update_question_schema()
        
        print("=" * 60)
        print("📝 질문 제출 요청 받음")
        print("=" * 60)
        
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        answer_method = request.form.get('answer_method', 'website').strip()  # 답변 받는 방법
        email = request.form.get('email', '').strip()  # 문의자 이메일
        phone = request.form.get('phone', '').strip()  # 문의자 전화번호
        kakao_name = request.form.get('kakao_name', '').strip()  # 카카오톡 이름/ID
        file = request.files.get('file')
        
        # 답변 받는 방법에 따른 필수 입력 검증
        if answer_method == 'email' and not email:
            return jsonify({'success': False, 'error': '이메일로 답변을 받으려면 이메일 주소를 입력해주세요.'}), 400
        if answer_method == 'kakao' and not phone:
            return jsonify({'success': False, 'error': '카카오톡으로 답변을 받으려면 전화번호를 입력해주세요.'}), 400
        
        print(f"제목: {title}")
        print(f"내용 길이: {len(content)} 문자")
        print(f"파일: {file.filename if file and file.filename else '없음'}")
        
        if file:
            print(f"파일 상세 정보:")
            print(f"  - 파일명: {file.filename}")
            print(f"  - Content-Type: {file.content_type}")
            print(f"  - Content-Length: {request.content_length if hasattr(request, 'content_length') else 'N/A'}")
        
        if not title or not content:
            return jsonify({'success': False, 'error': '제목과 내용을 입력해주세요.'}), 400
        
        # 파일 저장 (있는 경우)
        file_path = None
        if file and file.filename:
            # 원본 파일명과 확장자 확인
            original_filename = file.filename
            original_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            print(f"📎 파일 업로드 시도:")
            print(f"   원본 파일명: {original_filename}")
            print(f"   원본 확장자: {original_ext}")
            
            # secure_filename으로 안전한 파일명 생성
            filename = secure_filename(original_filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            print(f"   처리된 파일명: {filename}")
            print(f"   처리된 확장자: {file_ext}")
            
            # 확장자 확인 (원본과 처리된 파일명 모두 확인)
            if not original_ext and not file_ext:
                return jsonify({
                    'success': False, 
                    'error': '파일 확장자를 확인할 수 없습니다.'
                }), 400
            
            # 확장자 검증 (원본 확장자 우선, 없으면 처리된 확장자 사용)
            check_ext = original_ext if original_ext else file_ext
            print(f"   검증할 확장자: {check_ext}")
            print(f"   허용된 확장자 목록: {sorted(app.config['ALLOWED_EXTENSIONS'])}")
            
            if check_ext not in app.config['ALLOWED_EXTENSIONS']:
                allowed_exts = ', '.join(sorted(app.config['ALLOWED_EXTENSIONS']))
                print(f"❌ 지원하지 않는 파일 형식: {check_ext}")
                return jsonify({
                    'success': False, 
                    'error': f'지원하지 않는 파일 형식입니다. (확장자: {check_ext})\n허용된 형식: {allowed_exts}'
                }), 400
            
            print(f"✅ 파일 형식 확인 완료: {check_ext}")
            
            # 파일 크기 확인 (최대 2GB, 권장 1GB)
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            max_file_size = 2 * 1024 * 1024 * 1024  # 2GB (최대)
            recommended_size = 1 * 1024 * 1024 * 1024  # 1GB (권장)
            
            if file_size > max_file_size:
                file_size_mb = file_size / (1024 * 1024)
                max_size_mb = max_file_size / (1024 * 1024)
                return jsonify({
                    'success': False, 
                    'error': f'파일 크기는 {max_size_mb:.0f}MB (2GB)를 초과할 수 없습니다. (현재 파일: {file_size_mb:.2f}MB)'
                }), 400
            
            file_size_mb = file_size / (1024 * 1024)
            if file_size > recommended_size:
                print(f"⚠️ 큰 파일 업로드: {file_size_mb:.2f}MB (권장 크기 1GB 초과)")
            else:
                print(f"✅ 파일 크기 확인 완료: {file_size_mb:.2f}MB")
            
            # 디스크 공간 확인
            try:
                import shutil
                disk_usage = shutil.disk_usage(question_folder if os.path.exists(question_folder) else app.config['UPLOAD_FOLDER'])
                free_space = disk_usage.free
                free_space_gb = free_space / (1024 * 1024 * 1024)
                
                # 최소 5GB 여유 공간 필요 (2GB 파일 + 여유 공간)
                min_free_space = 5 * 1024 * 1024 * 1024  # 5GB
                if free_space < min_free_space:
                    print(f"⚠️ 디스크 공간 부족: {free_space_gb:.2f}GB (최소 5GB 필요)")
                    return jsonify({
                        'success': False,
                        'error': f'서버 디스크 공간이 부족합니다. (여유 공간: {free_space_gb:.2f}GB)'
                    }), 507  # 507 Insufficient Storage
                
                print(f"✅ 디스크 공간 확인: {free_space_gb:.2f}GB 여유")
            except Exception as disk_error:
                print(f"⚠️ 디스크 공간 확인 오류 (계속 진행): {disk_error}")
            
            # 질문 파일 저장 폴더 생성
            question_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'questions')
            os.makedirs(question_folder, exist_ok=True)
            
            # 고유 파일명 생성
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(question_folder, unique_filename)
            
            # 파일 저장 (스트리밍 방식으로 메모리 효율적으로 처리)
            try:
                # 파일을 청크 단위로 저장하여 메모리 사용량 최소화
                chunk_size = 8192  # 8KB 청크
                with open(file_path, 'wb') as f:
                    while True:
                        chunk = file.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                print(f"✅ 파일 저장 완료: {file_path}")
            except Exception as save_error:
                print(f"❌ 파일 저장 오류: {save_error}")
                # 저장 실패 시 부분적으로 저장된 파일 삭제
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
                return jsonify({
                    'success': False,
                    'error': f'파일 저장 중 오류가 발생했습니다: {str(save_error)}'
                }), 500
            
            # 상대 경로로 저장 (DB에 저장할 때)
            file_path = f"questions/{unique_filename}"
        
        # 노출/비노출 및 비밀번호 처리
        is_public = request.form.get('is_public', 'true').lower() == 'true'
        password = request.form.get('password', '').strip()
        password_hash = None
        
        if not is_public:
            if not password:
                return jsonify({'success': False, 'error': '비공개 질문은 비밀번호를 입력해주세요.'}), 400
            password_hash = generate_password_hash(password)
        
        # 질문 저장 (익명이므로 user_id는 None)
        # SQLite 직접 연결로 강제 저장 시도 (더 안정적)
        import sqlite3
        # Flask가 설정한 데이터베이스 경로 사용 (일관성 유지)
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        # sqlite:/// 경로에서 실제 파일 경로 추출
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '').replace('/', os.sep)
            # 절대 경로인 경우 (C:로 시작)
            if len(db_path) > 1 and db_path[1] == ':':
                pass  # 이미 절대 경로
            else:
                # 상대 경로인 경우 절대 경로로 변환
                db_path = os.path.abspath(db_path)
        else:
            # 기본 경로 시도
            possible_paths = [
                os.path.join(script_dir, 'onnuri_print_enhanced.db'),
                os.path.join(script_dir, 'instance', 'onnuri_print_enhanced.db'),
            ]
            db_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            if not db_path:
                instance_dir = os.path.join(script_dir, 'instance')
                os.makedirs(instance_dir, exist_ok=True)
                db_path = os.path.join(instance_dir, 'onnuri_print_enhanced.db')
        
        print(f"📁 [질문저장] 데이터베이스 경로: {db_path}")
        
        question_id = None
        save_success = False
        
        # 방법 1: SQLite 직접 연결로 저장 시도
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # question 테이블 존재 확인 및 생성
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question'")
            if not cursor.fetchone():
                print("📝 question 테이블이 없습니다. 생성 중...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS question (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        title VARCHAR(200) NOT NULL,
                        content TEXT NOT NULL,
                        file_path VARCHAR(500),
                        is_public INTEGER DEFAULT 1,
                        password_hash VARCHAR(200),
                        answer TEXT,
                        is_answered INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        answered_at DATETIME
                    )
                """)
                conn.commit()
                print("✅ question 테이블 생성 완료")
            
            # 컬럼 존재 여부 확인
            cursor.execute("PRAGMA table_info(question)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"📋 질문 저장 시도 - 현재 컬럼: {columns}")
            
            # 필요한 컬럼이 없으면 추가
            if 'file_path' not in columns:
                print("📝 file_path 컬럼 추가 중...")
                cursor.execute("ALTER TABLE question ADD COLUMN file_path VARCHAR(500)")
                conn.commit()
                columns.append('file_path')
                print("✅ file_path 컬럼 추가 완료")
            
            if 'is_public' not in columns:
                print("📝 is_public 컬럼 추가 중...")
                cursor.execute("ALTER TABLE question ADD COLUMN is_public INTEGER DEFAULT 1")
                conn.commit()
                cursor.execute("UPDATE question SET is_public = 1 WHERE is_public IS NULL")
                conn.commit()
                columns.append('is_public')
                print("✅ is_public 컬럼 추가 완료")
            
            if 'password_hash' not in columns:
                print("📝 password_hash 컬럼 추가 중...")
                cursor.execute("ALTER TABLE question ADD COLUMN password_hash VARCHAR(200)")
                conn.commit()
                columns.append('password_hash')
                print("✅ password_hash 컬럼 추가 완료")
            
            if 'email' not in columns:
                print("📝 email 컬럼 추가 중...")
                cursor.execute("ALTER TABLE question ADD COLUMN email VARCHAR(120)")
                conn.commit()
                columns.append('email')
                print("✅ email 컬럼 추가 완료")
            
            if 'phone' not in columns:
                print("📝 phone 컬럼 추가 중...")
                cursor.execute("ALTER TABLE question ADD COLUMN phone VARCHAR(20)")
                conn.commit()
                columns.append('phone')
                print("✅ phone 컬럼 추가 완료")
            
            if 'answer_sent_email' not in columns:
                print("📝 answer_sent_email 컬럼 추가 중...")
                cursor.execute("ALTER TABLE question ADD COLUMN answer_sent_email INTEGER DEFAULT 0")
                conn.commit()
                columns.append('answer_sent_email')
                print("✅ answer_sent_email 컬럼 추가 완료")
            
            if 'answer_sent_sms' not in columns:
                print("📝 answer_sent_sms 컬럼 추가 중...")
                cursor.execute("ALTER TABLE question ADD COLUMN answer_sent_sms INTEGER DEFAULT 0")
                conn.commit()
                columns.append('answer_sent_sms')
                print("✅ answer_sent_sms 컬럼 추가 완료")
            
            if 'answer_method' not in columns:
                print("📝 answer_method 컬럼 추가 중...")
                cursor.execute("ALTER TABLE question ADD COLUMN answer_method VARCHAR(20) DEFAULT 'website'")
                conn.commit()
                columns.append('answer_method')
                print("✅ answer_method 컬럼 추가 완료")
            
            if 'kakao_name' not in columns:
                print("📝 kakao_name 컬럼 추가 중...")
                cursor.execute("ALTER TABLE question ADD COLUMN kakao_name VARCHAR(50)")
                conn.commit()
                columns.append('kakao_name')
                print("✅ kakao_name 컬럼 추가 완료")
            
            # SQL 쿼리 동적 생성 (SQLite datetime 함수 사용)
            # email과 phone 컬럼 포함 여부 확인
            has_email = 'email' in columns
            has_phone = 'phone' in columns
            
            # 컬럼 목록과 값 목록 동적 생성
            insert_columns = ['user_id', 'title', 'content']
            insert_values = [None, title, content]
            
            if 'file_path' in columns:
                insert_columns.append('file_path')
                insert_values.append(file_path)
            
            if 'is_public' in columns:
                insert_columns.append('is_public')
                insert_values.append(1 if is_public else 0)
            
            if 'password_hash' in columns:
                insert_columns.append('password_hash')
                insert_values.append(password_hash)
            
            if has_email:
                insert_columns.append('email')
                insert_values.append(email if email else None)
            
            if has_phone:
                insert_columns.append('phone')
                insert_values.append(phone if phone else None)
            
            if 'answer_method' in columns:
                insert_columns.append('answer_method')
                insert_values.append(answer_method)
            
            if 'kakao_name' in columns:
                insert_columns.append('kakao_name')
                insert_values.append(kakao_name if kakao_name else None)
            
            insert_columns.extend(['is_answered', 'created_at'])
            insert_values.extend([0, 'datetime(\'now\')'])
            
            # SQL 쿼리 생성
            columns_str = ', '.join(insert_columns)
            placeholders = ', '.join(['?' if v != 'datetime(\'now\')' else 'datetime(\'now\')' for v in insert_values])
            # datetime('now')는 문자열이므로 실제 값에서 제거
            actual_values = [v for v in insert_values if v != 'datetime(\'now\')']
            
            query = f"INSERT INTO question ({columns_str}) VALUES ({placeholders})"
            cursor.execute(query, actual_values)
            
            conn.commit()
            question_id = cursor.lastrowid
            conn.close()
            save_success = True
            print(f"✅ [직접저장] 질문 저장 성공 (ID: {question_id})")
            
        except Exception as direct_error:
            print(f"⚠️ 직접 저장 실패: {direct_error}")
            import traceback
            traceback.print_exc()
            
            # 방법 2: SQLAlchemy를 통한 저장 (백업 방식)
            try:
                # is_public과 password_hash 필드가 있는지 확인하여 안전하게 생성
                question = Question(
                    user_id=None,
                    title=title,
                    content=content,
                    file_path=file_path if file_path else None
                )
                
                # is_public 필드가 있으면 설정
                try:
                    question.is_public = is_public
                except Exception:
                    # 컬럼이 없으면 무시 (기본값 True로 처리됨)
                    pass
                
                # password_hash 필드가 있으면 설정
                if password_hash:
                    try:
                        question.password_hash = password_hash
                    except Exception:
                        # 컬럼이 없으면 무시
                        pass
                
                db.session.add(question)
                db.session.commit()
                question_id = question.id
                save_success = True
                print(f"✅ [SQLAlchemy] 질문 저장 성공 (ID: {question_id})")
                
            except Exception as db_error:
                db.session.rollback()
                error_msg = str(db_error).lower()
                # 컬럼이 없는 경우를 감지하여 자동으로 컬럼 추가
                if 'no such column' in error_msg:
                    print(f"⚠️ 데이터베이스 컬럼 누락 감지: {error_msg}")
                    try:
                        from sqlalchemy import inspect, text
                        inspector = inspect(db.engine)
                        
                        if 'question' in inspector.get_table_names():
                            columns = [col['name'] for col in inspector.get_columns('question')]
                            print(f"📋 현재 question 테이블 컬럼: {columns}")
                            
                            # 누락된 컬럼 자동 추가
                            if 'file_path' not in columns:
                                print("📝 file_path 컬럼 자동 추가 중...")
                                db.session.execute(text('ALTER TABLE question ADD COLUMN file_path VARCHAR(500)'))
                                db.session.commit()
                                print("✅ file_path 컬럼 추가 완료")
                            
                            if 'is_public' not in columns:
                                print("📝 is_public 컬럼 자동 추가 중...")
                                db.session.execute(text('ALTER TABLE question ADD COLUMN is_public INTEGER DEFAULT 1'))
                                db.session.commit()
                                print("✅ is_public 컬럼 추가 완료")
                                db.session.execute(text('UPDATE question SET is_public = 1 WHERE is_public IS NULL'))
                                db.session.commit()
                            
                            if 'password_hash' not in columns:
                                print("📝 password_hash 컬럼 자동 추가 중...")
                                db.session.execute(text('ALTER TABLE question ADD COLUMN password_hash VARCHAR(200)'))
                                db.session.commit()
                                print("✅ password_hash 컬럼 추가 완료")
                            
                            # 컬럼 추가 후 다시 시도
                            print("🔄 질문 저장 재시도 중...")
                            question = Question(
                                user_id=None,
                                title=title,
                                content=content,
                                file_path=file_path
                            )
                            
                            # 컬럼이 있으면 설정
                            updated_columns = [col['name'] for col in inspector.get_columns('question')]
                            if 'is_public' in updated_columns:
                                question.is_public = is_public
                            if password_hash and 'password_hash' in updated_columns:
                                question.password_hash = password_hash
                            
                            db.session.add(question)
                            db.session.commit()
                            question_id = question.id
                            save_success = True
                            print(f"✅ 질문 저장 성공 (ID: {question.id})")
                        else:
                            raise db_error
                    except Exception as auto_fix_error:
                        print(f"⚠️ 자동 수정 실패: {auto_fix_error}")
                        import traceback
                        traceback.print_exc()
                        db.session.rollback()
                        raise db_error
                else:
                    raise db_error
        
        # 저장 성공 여부 확인
        if save_success and question_id:
            return jsonify({
                'success': True,
                'message': '질문이 성공적으로 등록되었습니다.',
                'question_id': question_id
            })
        else:
            # 저장 실패 시 상세 오류 로그
            print(f"❌ 질문 저장 실패 - save_success: {save_success}, question_id: {question_id}")
            return jsonify({
                'success': False,
                'error': '질문 저장에 실패했습니다. 데이터베이스를 확인해주세요.'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ 질문 제출 오류: {e}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"상세 오류:\n{error_trace}")
        
        # 사용자에게는 간단한 메시지만 표시
        error_message = str(e)
        print(f"❌ 질문 제출 최종 오류: {error_message}")
        
        # 데이터베이스 스키마 문제인 경우 자동 수정 시도
        if 'no such column' in error_message.lower():
            print("🔄 데이터베이스 스키마 자동 수정 시도...")
            try:
                update_question_schema()
                # 수정 후 다시 저장 시도
                import sqlite3
                # Flask가 설정한 데이터베이스 경로 사용 (일관성 유지)
                db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
                # sqlite:/// 경로에서 실제 파일 경로 추출
                if db_uri.startswith('sqlite:///'):
                    db_path = db_uri.replace('sqlite:///', '').replace('/', os.sep)
                    # 절대 경로인 경우 (C:로 시작)
                    if len(db_path) > 1 and db_path[1] == ':':
                        pass  # 이미 절대 경로
                    else:
                        # 상대 경로인 경우 절대 경로로 변환
                        db_path = os.path.abspath(db_path)
                else:
                    # 기본 경로 시도
                    possible_paths = [
                        os.path.join(script_dir, 'onnuri_print_enhanced.db'),
                        os.path.join(script_dir, 'instance', 'onnuri_print_enhanced.db'),
                    ]
                    db_path = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            db_path = path
                            break
                    if not db_path:
                        instance_dir = os.path.join(script_dir, 'instance')
                        os.makedirs(instance_dir, exist_ok=True)
                        db_path = os.path.join(instance_dir, 'onnuri_print_enhanced.db')
                
                print(f"📁 [자동수정] 데이터베이스 경로: {db_path}")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("PRAGMA table_info(question)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # 최소한의 컬럼만으로 저장 시도
                if 'title' in columns and 'content' in columns:
                    cursor.execute("""
                        INSERT INTO question (user_id, title, content, is_answered, created_at)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """, (None, title, content, 0))
                    conn.commit()
                    question_id = cursor.lastrowid
                    conn.close()
                    print(f"✅ [자동수정후저장] 질문 저장 성공 (ID: {question_id})")
                    return jsonify({
                        'success': True,
                        'message': '질문이 성공적으로 등록되었습니다.',
                        'question_id': question_id
                    })
            except Exception as auto_fix_error:
                print(f"⚠️ 자동 수정 후 저장 실패: {auto_fix_error}")
        
        # 일반적인 오류 메시지
        error_message = '질문 등록 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
        return jsonify({'success': False, 'error': error_message}), 500

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """등록된 질문 목록 가져오기 (공개 질문만, 페이지네이션 지원)"""
    try:
        # Question 테이블 존재 여부 확인
        from sqlalchemy import inspect
        try:
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
        except Exception as inspect_error:
            print(f"⚠️ 테이블 목록 조회 실패: {inspect_error}")
            # 오류 발생 시에도 빈 목록 반환하여 게시판이 작동하도록 함
            return jsonify({
                'success': True, 
                'questions': [],
                'has_next': False,
                'current_page': 1
            })
        
        if 'question' not in table_names:
            # 테이블이 없으면 빈 목록 반환
            print("⚠️ question 테이블이 존재하지 않습니다. 빈 목록을 반환합니다.")
            return jsonify({
                'success': True, 
                'questions': [],
                'has_next': False,
                'current_page': 1
            })
        
        # 페이지네이션 파라미터
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 기본 쿼리 (공개 질문만)
        base_query = None
        try:
            # SQLite는 BOOLEAN을 INTEGER로 저장하므로 여러 방법으로 필터링 시도
            # 방법 1: 직접 필터링 시도
            try:
                base_query = Question.query.filter(
                    (Question.is_public == True) | (Question.is_public == 1) | (Question.is_public.is_(None))
                ).order_by(Question.created_at.desc())
            except Exception:
                # 필터링 실패 시 모든 질문 조회 후 Python에서 필터링
                base_query = Question.query.order_by(Question.created_at.desc())
            
            # 페이지네이션
            pagination = base_query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            questions = pagination.items
            
            # Python에서 공개 질문만 필터링 (이중 체크)
            public_questions = []
            for q in questions:
                is_public = True
                try:
                    is_public_attr = getattr(q, 'is_public', None)
                    if is_public_attr is not None:
                        if isinstance(is_public_attr, int):
                            is_public = bool(is_public_attr)
                        elif isinstance(is_public_attr, bool):
                            is_public = is_public_attr
                        else:
                            is_public = True
                    # None이면 기본값 True (공개)
                except Exception:
                    is_public = True
                
                if is_public:
                    public_questions.append(q)
            
            questions = public_questions
            has_next = pagination.has_next and len(public_questions) > 0
        except Exception as query_error:
            print(f"⚠️ 질문 쿼리 오류: {query_error}")
            import traceback
            traceback.print_exc()
            # 쿼리 실패 시 빈 목록 반환
            return jsonify({
                'success': True, 
                'questions': [],
                'has_next': False,
                'current_page': page
            })
        
        questions_data = []
        for q in questions:
            try:
                # is_public 확인 (기본값 True)
                is_public = True
                try:
                    is_public_attr = getattr(q, 'is_public', None)
                    if is_public_attr is not None:
                        # SQLite는 BOOLEAN을 INTEGER로 저장하므로 변환 필요
                        if isinstance(is_public_attr, int):
                            is_public = bool(is_public_attr)
                        elif isinstance(is_public_attr, bool):
                            is_public = is_public_attr
                        else:
                            is_public = True
                except Exception as attr_error:
                    # 속성이 없거나 접근 불가능하면 기본값 True 사용
                    is_public = True
                
                # 비공개 질문은 제외 (이중 체크)
                if not is_public:
                    continue
                
                questions_data.append({
                    'id': q.id,
                    'title': q.title,
                    'content': q.content,
                    'has_file': bool(q.file_path) if q.file_path else False,
                    'file_path': q.file_path if q.file_path else None,
                    'is_answered': bool(q.is_answered) if q.is_answered else False,
                    'answer': q.answer if (q.is_answered and q.answer) else None,
                    'created_at': q.created_at.strftime('%Y-%m-%d %H:%M') if q.created_at else None
                })
            except Exception as item_error:
                print(f"⚠️ 질문 항목 처리 오류 (ID: {getattr(q, 'id', 'unknown')}): {item_error}")
                import traceback
                traceback.print_exc()
                continue
        
        # has_next 계산
        calculated_has_next = False
        if 'has_next' in locals():
            calculated_has_next = has_next
        elif len(questions_data) >= per_page and base_query:
            # 다음 페이지가 있을 가능성 체크
            try:
                next_page_query = base_query.paginate(page=page+1, per_page=1, error_out=False)
                if next_page_query.items:
                    # 다음 페이지의 항목 중 공개 질문이 있는지 확인
                    for q in next_page_query.items:
                        is_public = True
                        try:
                            is_public_attr = getattr(q, 'is_public', None)
                            if is_public_attr is not None:
                                if isinstance(is_public_attr, int):
                                    is_public = bool(is_public_attr)
                                elif isinstance(is_public_attr, bool):
                                    is_public = is_public_attr
                        except:
                            pass
                        if is_public:
                            calculated_has_next = True
                            break
            except Exception as e:
                print(f"⚠️ has_next 계산 오류: {e}")
                calculated_has_next = False
        
        return jsonify({
            'success': True, 
            'questions': questions_data,
            'current_page': page,
            'per_page': per_page,
            'total': len(questions_data),  # 실제 반환된 항목 수
            'pages': max(1, (len(questions_data) + per_page - 1) // per_page) if questions_data else 1,
            'has_next': calculated_has_next,
            'has_prev': page > 1
        })
        
    except Exception as e:
        print(f"⚠️ 질문 목록 조회 오류: {e}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"상세 오류:\n{error_trace}")
        # 오류 발생 시에도 빈 목록 반환 (404 방지)
        return jsonify({
            'success': True, 
            'questions': [],
            'has_next': False,
            'current_page': 1
        })

@app.route('/api/question/<int:question_id>', methods=['POST'])
def view_private_question(question_id):
    """비공개 질문 조회 (비밀번호 확인)"""
    try:
        # JSON 또는 form 데이터에서 비밀번호 가져오기
        if request.is_json:
            password = request.json.get('password', '')
        else:
            password = request.form.get('password', '')
        
        question = Question.query.get_or_404(question_id)
        
        # is_public 확인 (기본값 True)
        is_public = True
        try:
            is_public_attr = getattr(question, 'is_public', None)
            if is_public_attr is not None:
                # SQLite는 BOOLEAN을 INTEGER로 저장하므로 변환 필요
                if isinstance(is_public_attr, int):
                    is_public = bool(is_public_attr)
                elif isinstance(is_public_attr, bool):
                    is_public = is_public_attr
                else:
                    is_public = True
        except Exception:
            # 속성이 없거나 접근 불가능하면 기본값 True 사용
            is_public = True
        
        # 공개 질문이면 바로 반환
        if is_public:
            return jsonify({
                'success': True,
                'question': {
                    'id': question.id,
                    'title': question.title,
                    'content': question.content,
                    'has_file': bool(question.file_path),
                    'file_path': question.file_path if question.file_path else None,
                    'is_answered': question.is_answered,
                    'answer': question.answer if question.is_answered else None,
                    'created_at': question.created_at.strftime('%Y-%m-%d %H:%M') if question.created_at else None
                }
            })
        
        # 비공개 질문은 비밀번호 확인 필요
        if not password:
            return jsonify({'success': False, 'error': '비밀번호를 입력해주세요.'}), 400
        
        password_hash = getattr(question, 'password_hash', None)
        if not password_hash:
            return jsonify({'success': False, 'error': '비밀번호가 설정되지 않은 질문입니다.'}), 400
        
        if not check_password_hash(password_hash, password):
            return jsonify({'success': False, 'error': '비밀번호가 올바르지 않습니다.'}), 401
        
        return jsonify({
            'success': True,
            'question': {
                'id': question.id,
                'title': question.title,
                'content': question.content,
                'has_file': bool(question.file_path),
                'file_path': question.file_path if question.file_path else None,
                'is_answered': question.is_answered,
                'answer': question.answer if question.is_answered else None,
                'created_at': question.created_at.strftime('%Y-%m-%d %H:%M') if question.created_at else None
            }
        })
        
    except Exception as e:
        print(f"⚠️ 비공개 질문 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '질문 조회 중 오류가 발생했습니다.'}), 500

# Q&A 페이지 (공개 접근)
@app.route('/board')
@app.route('/board/<int:category_id>')
def board(category_id=None):
    """게시판 목록 페이지"""
    try:
        # 활성화된 카테고리 가져오기
        categories = BoardCategory.query.filter_by(is_active=True).order_by(BoardCategory.display_order, BoardCategory.name).all()
        
        # 카테고리 선택 (기본값: 첫 번째 카테고리)
        if category_id:
            selected_category = BoardCategory.query.filter_by(id=category_id, is_active=True).first_or_404()
        elif categories:
            selected_category = categories[0]
        else:
            selected_category = None
        
        # 페이지네이션
        page = request.args.get('page', 1, type=int)
        per_page = 15
        
        if selected_category:
            # 공지사항 먼저 (상단 고정)
            notice_posts = BoardPost.query.filter_by(
                category_id=selected_category.id,
                is_active=True,
                is_notice=True
            ).order_by(BoardPost.is_pinned.desc(), BoardPost.created_at.desc()).all()
            
            # 일반 게시글
            posts_query = BoardPost.query.filter_by(
                category_id=selected_category.id,
                is_active=True,
                is_notice=False
            ).order_by(BoardPost.is_pinned.desc(), BoardPost.created_at.desc())
            
            posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
        else:
            # 카테고리가 없거나 선택되지 않았을 때 모든 게시글 표시 (공지사항 제외)
            notice_posts = []
            posts_query = BoardPost.query.filter_by(
                is_active=True,
                is_notice=False
            ).order_by(BoardPost.is_pinned.desc(), BoardPost.created_at.desc())
            
            posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('board.html',
                             categories=categories,
                             selected_category=selected_category,
                             notice_posts=notice_posts,
                             posts=posts)
    except Exception as e:
        print(f"⚠️ 게시판 목록 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return render_template('board.html',
                             categories=[],
                             selected_category=None,
                             notice_posts=[],
                             posts=None)

# 한글 파일명 이미지 처리 라우트 (Flask 기본 static보다 우선)
@app.route('/static/images/<path:filename>')
def serve_static_image(filename):
    """한글 파일명을 포함한 이미지 파일 제공"""
    try:
        # URL 디코딩
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        # static/images 폴더 경로
        images_dir = os.path.join(static_dir_abs, 'images')
        file_path = os.path.join(images_dir, decoded_filename)
        
        # 파일 존재 확인
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(images_dir, decoded_filename)
        else:
            # 파일이 없으면 Flask 기본 static 처리로 넘김
            from flask import send_from_directory as flask_send_from_directory
            try:
                return flask_send_from_directory(images_dir, decoded_filename)
            except:
                print(f"⚠️ 이미지 파일을 찾을 수 없습니다: {file_path}")
                print(f"   찾은 파일 목록: {os.listdir(images_dir) if os.path.exists(images_dir) else '폴더 없음'}")
                return "File not found", 404
    except Exception as e:
        print(f"⚠️ 이미지 제공 오류: {e}")
        import traceback
        traceback.print_exc()
        return "Error", 500

# 게시판 업로드 파일 제공 라우트
@app.route('/uploads/<path:filename>')
def serve_upload_file(filename):
    """게시판 등에서 업로드된 파일 제공"""
    try:
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        # uploads 폴더 경로
        uploads_dir = app.config['UPLOAD_FOLDER']
        file_path = os.path.join(uploads_dir, decoded_filename)
        
        # 파일 존재 확인
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(uploads_dir, decoded_filename)
        else:
            print(f"⚠️ 업로드 파일을 찾을 수 없습니다: {file_path}")
            return "File not found", 404
    except Exception as e:
        print(f"⚠️ 업로드 파일 제공 오류: {e}")
        import traceback
        traceback.print_exc()
        return "Error", 500

@app.route('/board/post/<int:post_id>')
def board_detail(post_id):
    """게시글 상세 보기"""
    try:
        post = BoardPost.query.get_or_404(post_id)
        
        # 조회수 증가
        post.view_count += 1
        db.session.commit()
        
        # 댓글 가져오기
        comments = BoardComment.query.filter_by(post_id=post_id).order_by(BoardComment.created_at.asc()).all()
        
        # 관리자 여부 확인
        is_admin = False
        try:
            if current_user.is_authenticated:
                is_admin = bool(current_user.is_admin)
        except:
            pass
        
        return render_template('board_detail.html', post=post, comments=comments, is_admin=is_admin)
    except Exception as e:
        print(f"⚠️ 게시글 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        flash('게시글을 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('board'))

@app.route('/board/write', methods=['GET', 'POST'])
def board_write():
    """게시글 작성"""
    try:
        if request.method == 'POST':
            category_id = request.form.get('category_id', type=int)
            author_name = request.form.get('author_name', '').strip()
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            files = request.files.getlist('files')  # 여러 파일 가져오기
            
            if not category_id or not author_name or not title or not content:
                flash('모든 필수 항목을 입력해주세요.', 'error')
                return redirect(url_for('board_write'))
            
            # 여러 파일 저장 (이미지 파일만 허용)
            file_paths = []
            if files and any(f.filename for f in files):
                import time
                import json
                timestamp = int(time.time())
                
                for idx, file in enumerate(files):
                    if not file.filename:
                        continue
                    
                    # 이미지 파일인지 확인
                    if not allowed_image_file(file.filename):
                        flash(f'"{file.filename}"은(는) 이미지 파일만 업로드 가능합니다. (JPG, PNG, GIF, WEBP 등)', 'error')
                        continue
                    
                    # 파일 저장
                    filename = secure_filename(file.filename)
                    name, ext = os.path.splitext(filename)
                    # 중복 방지를 위한 타임스탬프와 인덱스 추가
                    unique_filename = f"{name}_{timestamp}_{idx}{ext}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'board', unique_filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    file_paths.append(os.path.join('board', unique_filename))
                
                if files and any(f.filename for f in files) and not file_paths:
                    flash('유효한 이미지 파일이 없습니다.', 'error')
                    return redirect(url_for('board_write'))
            
            # 파일 경로를 JSON 배열로 저장 (단일 파일도 배열로 저장하여 호환성 유지)
            import json
            file_path = json.dumps(file_paths) if file_paths else None
            
            # 게시글 저장
            try:
                user_id = current_user.id if current_user.is_authenticated else None
            except:
                user_id = None
            
            post = BoardPost(
                category_id=category_id,
                user_id=user_id,
                author_name=author_name,
                title=title,
                content=content,
                file_path=file_path
            )
            
            db.session.add(post)
            db.session.commit()
            
            flash('게시글이 등록되었습니다.', 'success')
            return redirect(url_for('board_detail', post_id=post.id))
        
        # GET 요청: 작성 폼
        # 관리자 여부 확인
        is_admin = False
        try:
            if current_user.is_authenticated:
                is_admin = bool(current_user.is_admin)
        except:
            pass
        
        # 카테고리 필터링: 관리자가 아니면 관리자 전용 카테고리 제외
        if is_admin:
            categories = BoardCategory.query.filter_by(is_active=True).order_by(BoardCategory.display_order, BoardCategory.name).all()
        else:
            categories = BoardCategory.query.filter_by(is_active=True, is_admin_only=False).order_by(BoardCategory.display_order, BoardCategory.name).all()
        
        # 기본 카테고리 찾기: "자유게시판" 또는 "사용후기" 또는 첫 번째 일반 카테고리
        default_category_id = None
        for category in categories:
            if category.name in ['자유게시판', '사용후기']:
                default_category_id = category.id
                break
        if not default_category_id and categories:
            default_category_id = categories[0].id
        
        return render_template('board_write.html', categories=categories, is_admin=is_admin, default_category_id=default_category_id)
    except Exception as e:
        print(f"⚠️ 게시글 작성 오류: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        flash('게시글 작성 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('board'))

@app.route('/api/board/<int:post_id>/comments', methods=['GET'])
def get_board_comments(post_id):
    """게시글 댓글 목록 조회"""
    try:
        comments = BoardComment.query.filter_by(post_id=post_id).order_by(BoardComment.created_at.asc()).all()
        comments_data = []
        for comment in comments:
            user = User.query.get(comment.user_id)
            comments_data.append({
                'id': comment.id,
                'content': comment.content,
                'author_name': user.username if user else '관리자',
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else '',
                'is_admin': True  # 댓글은 관리자만 작성 가능
            })
        return jsonify({'success': True, 'comments': comments_data})
    except Exception as e:
        print(f"⚠️ 댓글 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '댓글을 불러오는 중 오류가 발생했습니다.'}), 500

@app.route('/api/board/<int:post_id>/comments', methods=['POST'])
@login_required
def add_board_comment(post_id):
    """게시글 댓글 작성 (관리자 전용)"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': '관리자만 댓글을 작성할 수 있습니다.'}), 403
        
        # 게시글 존재 확인
        post = BoardPost.query.get_or_404(post_id)
        
        # 댓글 내용 가져오기
        if request.is_json:
            data = request.json
            content = data.get('content', '').strip()
        else:
            content = request.form.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': '댓글 내용을 입력해주세요.'}), 400
        
        # 댓글 저장
        comment = BoardComment(
            post_id=post_id,
            user_id=current_user.id,
            content=content
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # 댓글 데이터 반환
        comment_data = {
            'id': comment.id,
            'content': comment.content,
            'author_name': current_user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else '',
            'is_admin': True
        }
        
        return jsonify({'success': True, 'comment': comment_data})
    except Exception as e:
        print(f"⚠️ 댓글 작성 오류: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': '댓글 작성 중 오류가 발생했습니다.'}), 500

@app.route('/qa')
@app.route('/qna')
def qa():
    """Q&A 페이지 - 공개 접근"""
    try:
        print("=" * 60)
        print("📄 Q&A 페이지 렌더링 시작...")
        template_path = os.path.join(app.template_folder, 'qa.html')
        print(f"📁 템플릿 경로: {template_path}")
        print(f"📁 템플릿 존재 여부: {os.path.exists(template_path)}")
        if os.path.exists(template_path):
            file_size = os.path.getsize(template_path)
            print(f"📊 템플릿 파일 크기: {file_size} bytes")
        print("=" * 60)
        return render_template('qa.html')
    except Exception as e:
        print(f"⚠️ Q&A 페이지 오류: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Q&A 페이지 오류</h1><p>{str(e)}</p>", 500

# 관리자 Q&A 관리 기능
@app.route('/admin/questions')
@login_required
def admin_questions():
    """관리자 Q&A 관리 페이지"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            flash('관리자만 접근할 수 있습니다.', 'error')
            return redirect(url_for('index'))
        
        # 템플릿 렌더링
        return render_template('admin_questions.html')
    except Exception as e:
        print(f"⚠️ Q&A 관리 페이지 오류: {e}")
        import traceback
        traceback.print_exc()
        flash('Q&A 관리 페이지를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/api/admin/questions', methods=['GET'])
@login_required
def get_admin_questions():
    """관리자용 질문 목록 (모든 질문, 공개/비공개 모두) - 강화된 오류 처리"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            print("⚠️ 비관리자 접근 시도")
            return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
        
        print("=" * 60)
        print("📋 관리자 질문 목록 조회 시작...")
        print(f"👤 현재 사용자: {current_user.username}, 관리자: {current_user.is_admin}")
        
        # 데이터베이스 스키마 강제 업데이트
        try:
            update_question_schema()
            print("✅ 데이터베이스 스키마 업데이트 완료")
        except Exception as schema_error:
            print(f"⚠️ 스키마 업데이트 오류 (계속 진행): {schema_error}")
        
        # Question 테이블 존재 여부 확인
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
            print(f"📋 데이터베이스 테이블 목록: {table_names}")
        except Exception as inspect_error:
            print(f"⚠️ 테이블 목록 확인 오류: {inspect_error}")
            # 오류가 있어도 계속 진행
            table_names = []
        
        if 'question' not in table_names:
            print("⚠️ question 테이블이 존재하지 않습니다.")
            print("📝 테이블을 생성합니다...")
            try:
                db.create_all()
                print("✅ 테이블 생성 완료")
            except Exception as e:
                print(f"⚠️ 테이블 생성 오류: {e}")
                import traceback
                traceback.print_exc()
            
            return jsonify({
                'success': True,
                'questions': [],
                'total': 0,
                'message': '질문 테이블이 아직 생성되지 않았습니다. 질문을 등록하면 테이블이 자동으로 생성됩니다.'
            })
        
        # 모든 질문 조회 (공개/비공개 구분 없이) - 강화된 오류 처리
        questions = []
        try:
            questions = Question.query.order_by(Question.created_at.desc()).all()
            print(f"📊 총 질문 개수: {len(questions)}")
            
            if len(questions) == 0:
                print("ℹ️ 데이터베이스에 등록된 질문이 없습니다.")
                return jsonify({
                    'success': True,
                    'questions': [],
                    'total': 0
                })
        except Exception as query_error:
            print(f"❌ 질문 조회 오류: {query_error}")
            import traceback
            traceback.print_exc()
            # 오류가 있어도 빈 목록 반환 (서버가 중단되지 않도록)
            return jsonify({
                'success': True,
                'questions': [],
                'total': 0,
                'message': f'질문 조회 중 오류가 발생했습니다: {str(query_error)}'
            })
        
        questions_data = []
        processed_count = 0
        error_count = 0
        
        for q in questions:
            try:
                # 기본 정보 안전하게 가져오기
                question_id = None
                title = '제목 없음'
                content = ''
                file_path = None
                is_public = True
                is_answered = False
                answer = None
                email = None
                phone = None
                answer_method = 'website'
                kakao_name = None
                created_at = None
                answered_at = None
                
                # ID
                try:
                    question_id = q.id if hasattr(q, 'id') and q.id else None
                except:
                    question_id = None
                
                # 제목
                try:
                    title = q.title if hasattr(q, 'title') and q.title else '제목 없음'
                except:
                    title = '제목 없음'
                
                # 내용
                try:
                    content = q.content if hasattr(q, 'content') and q.content else ''
                except:
                    content = ''
                
                # 파일 경로
                try:
                    file_path = q.file_path if hasattr(q, 'file_path') and q.file_path else None
                except:
                    file_path = None
                
                # is_public 확인
                try:
                    if hasattr(q, 'is_public'):
                        is_public_attr = q.is_public
                        if is_public_attr is not None:
                            if isinstance(is_public_attr, int):
                                is_public = bool(is_public_attr)
                            elif isinstance(is_public_attr, bool):
                                is_public = is_public_attr
                except:
                    is_public = True
                
                # is_answered 확인
                try:
                    if hasattr(q, 'is_answered'):
                        is_answered_attr = q.is_answered
                        if is_answered_attr is not None:
                            if isinstance(is_answered_attr, int):
                                is_answered = bool(is_answered_attr)
                            elif isinstance(is_answered_attr, bool):
                                is_answered = is_answered_attr
                except:
                    is_answered = False
                
                # 답변 내용
                try:
                    if is_answered and hasattr(q, 'answer') and q.answer:
                        answer = q.answer
                except:
                    answer = None
                
                # 이메일
                try:
                    if hasattr(q, 'email'):
                        email = q.email
                except:
                    email = None
                
                # 전화번호
                try:
                    if hasattr(q, 'phone'):
                        phone = q.phone
                except:
                    phone = None
                
                # 답변 방법
                try:
                    if hasattr(q, 'answer_method'):
                        answer_method = q.answer_method or 'website'
                    else:
                        answer_method = 'website'
                except:
                    answer_method = 'website'
                
                # 카카오톡 이름
                try:
                    if hasattr(q, 'kakao_name'):
                        kakao_name = q.kakao_name
                except:
                    kakao_name = None
                
                # 생성일
                try:
                    if hasattr(q, 'created_at') and q.created_at:
                        created_at = q.created_at.strftime('%Y-%m-%d %H:%M')
                except:
                    created_at = None
                
                # 답변일
                try:
                    if hasattr(q, 'answered_at') and q.answered_at:
                        answered_at = q.answered_at.strftime('%Y-%m-%d %H:%M')
                except:
                    answered_at = None
                
                # 질문 데이터 추가
                questions_data.append({
                    'id': question_id,
                    'title': title,
                    'content': content,
                    'has_file': bool(file_path),
                    'file_path': file_path,
                    'is_public': is_public,
                    'is_answered': is_answered,
                    'answer': answer,
                    'email': email,
                    'phone': phone,
                    'answer_method': answer_method,
                    'kakao_name': kakao_name,
                    'created_at': created_at,
                    'answered_at': answered_at
                })
                processed_count += 1
                
            except Exception as item_error:
                error_count += 1
                question_id_str = 'unknown'
                try:
                    question_id_str = str(q.id) if hasattr(q, 'id') else 'unknown'
                except:
                    pass
                print(f"⚠️ 질문 항목 처리 오류 (ID: {question_id_str}): {item_error}")
                import traceback
                traceback.print_exc()
                # 오류가 있어도 계속 진행 (다음 질문 처리)
                continue
        
        print(f"✅ 처리 완료: 성공 {processed_count}개, 오류 {error_count}개")
        print(f"✅ 최종 처리된 질문 개수: {len(questions_data)}")
        print("=" * 60)
        
        return jsonify({
            'success': True,
            'questions': questions_data,
            'total': len(questions_data)
        })
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ 관리자 질문 목록 조회 중 치명적 오류 발생")
        print(f"오류 내용: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        
        # 치명적 오류가 있어도 빈 목록 반환 (500 오류 대신 200 OK)
        # 서버가 중단되지 않도록 처리
        return jsonify({
            'success': True,
            'questions': [],
            'total': 0,
            'message': '질문 목록을 불러오는 중 오류가 발생했습니다. 서버 로그를 확인해주세요.'
        })

@app.route('/api/admin/question/<int:question_id>/answer', methods=['POST'])
@login_required
def answer_question(question_id):
    """관리자가 질문에 답변 작성/수정 및 전송"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
    
    try:
        question = Question.query.get_or_404(question_id)
        
        # JSON 또는 form 데이터에서 답변 가져오기
        if request.is_json:
            answer = request.json.get('answer', '').strip()
            send_email = request.json.get('send_email', False)
            send_sms = request.json.get('send_sms', False)
        else:
            answer = request.form.get('answer', '').strip()
            send_email = request.form.get('send_email', 'false').lower() == 'true'
            send_sms = request.form.get('send_sms', 'false').lower() == 'true'
        
        if not answer:
            return jsonify({'success': False, 'error': '답변 내용을 입력해주세요.'}), 400
        
        # 답변 저장
        question.answer = answer
        question.is_answered = True
        question.answered_at = datetime.utcnow()
        
        # 질문자가 선택한 답변 받는 방법 확인
        answer_method = getattr(question, 'answer_method', 'website') if hasattr(question, 'answer_method') else 'website'
        
        # 이메일 전송 (이메일 방법 선택 시 또는 체크박스 선택 시)
        email_sent = False
        if (answer_method == 'email' or send_email) and question.email:
            try:
                email_sent = send_answer_email(question.email, question.title, answer)
                if email_sent:
                    question.answer_sent_email = True
                    print(f"✅ 답변 이메일 전송 성공: {question.email}")
                else:
                    print(f"⚠️ 답변 이메일 전송 실패: {question.email}")
            except Exception as email_error:
                print(f"⚠️ 답변 이메일 전송 오류: {email_error}")
        
        # 카카오톡 기능 제거됨 - 이메일 전송만 사용
        
        db.session.commit()
        
        message = '답변이 성공적으로 저장되었습니다.'
        if email_sent:
            message += ' 이메일로 전송되었습니다.'
        elif (answer_method == 'email' or send_email) and question.email:
            # 이메일 전송을 시도했지만 실패한 경우
            message += ' (이메일 전송 실패 - 서버 로그 확인 필요)'
        
        return jsonify({
            'success': True,
            'message': message,
            'email_sent': email_sent,
            'question': {
                'id': question.id,
                'answer': question.answer,
                'is_answered': question.is_answered,
                'answered_at': question.answered_at.strftime('%Y-%m-%d %H:%M') if question.answered_at else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ 답변 저장 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '답변 저장 중 오류가 발생했습니다.'}), 500

@app.route('/api/admin/test-email', methods=['POST'])
@login_required
def test_email():
    """이메일 전송 테스트 (관리자 전용)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
    
    try:
        if request.is_json:
            test_email = request.json.get('email', '').strip()
            test_subject = request.json.get('subject', '[온누리인쇄나라] 이메일 전송 테스트').strip()
            test_message = request.json.get('message', '이것은 이메일 전송 테스트 메시지입니다.').strip()
        else:
            test_email = request.form.get('email', '').strip()
            test_subject = request.form.get('subject', '[온누리인쇄나라] 이메일 전송 테스트').strip()
            test_message = request.form.get('message', '이것은 이메일 전송 테스트 메시지입니다.').strip()
        
        if not test_email:
            return jsonify({'success': False, 'error': '테스트 이메일 주소를 입력해주세요.'}), 400
        
        # 이메일 형식 검증
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, test_email):
            return jsonify({'success': False, 'error': '올바른 이메일 주소 형식을 입력해주세요.'}), 400
        
        print("=" * 60)
        print("📧 이메일 전송 테스트 시작...")
        print(f"   수신자: {test_email}")
        print(f"   제목: {test_subject}")
        print("=" * 60)
        
        # HTML 이메일 생성
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Malgun Gothic', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .message {{ background-color: white; padding: 15px; border-left: 4px solid #007bff; margin-top: 15px; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>온누리인쇄나라</h2>
                </div>
                <div class="content">
                    <p>안녕하세요.</p>
                    <p>이것은 <strong>이메일 전송 테스트</strong> 메시지입니다.</p>
                    <div class="message">
                        <p><strong>테스트 메시지:</strong></p>
                        <p>{test_message.replace(chr(10), '<br>')}</p>
                    </div>
                    <p style="margin-top: 20px; color: #28a745; font-weight: bold;">
                        ✅ 이메일이 정상적으로 수신되었다면 SMTP 설정이 올바르게 작동하는 것입니다.
                    </p>
                </div>
                <div class="footer">
                    <p>온누리인쇄나라</p>
                    <p>전화: 02-6338-7123 | 이메일: print7123@naver.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
온누리인쇄나라

안녕하세요.

이것은 이메일 전송 테스트 메시지입니다.

테스트 메시지:
{test_message}

✅ 이메일이 정상적으로 수신되었다면 SMTP 설정이 올바르게 작동하는 것입니다.

온누리인쇄나라
전화: 02-6338-7123
이메일: print7123@naver.com
        """
        
        # 이메일 전송
        email_sent = send_html_email(test_email, test_subject, html_content, text_content)
        
        if email_sent:
            print(f"✅ 테스트 이메일 전송 성공: {test_email}")
            return jsonify({
                'success': True,
                'message': f'테스트 이메일이 {test_email}로 전송되었습니다.'
            })
        else:
            print(f"❌ 테스트 이메일 전송 실패: {test_email}")
            return jsonify({
                'success': False,
                'error': '이메일 전송에 실패했습니다. 서버 로그를 확인하거나 SMTP 설정을 확인하세요.'
            }), 500
            
    except Exception as e:
        print(f"❌ 이메일 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'이메일 테스트 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/admin/email-config', methods=['GET', 'POST'])
@login_required
def email_config():
    """이메일 설정 조회 및 업데이트 (관리자 전용)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
    
    if request.method == 'GET':
        # 현재 이메일 설정 조회
        try:
            # email_config.py에서 설정 읽기
            email_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_config.py')
            
            config = {
                'mail_server': app.config.get('MAIL_SERVER', 'smtp.naver.com'),
                'mail_port': app.config.get('MAIL_PORT', 587),
                'mail_username': app.config.get('MAIL_USERNAME', 'print7123@naver.com'),
                'password_set': False
            }
            
            # email_config.py 파일에서 비밀번호 설정 여부 확인
            if os.path.exists(email_config_path):
                try:
                    with open(email_config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 비밀번호가 설정되어 있는지 확인
                        if "MAIL_PASSWORD = 'your-app-password'" not in content:
                            # 실제 비밀번호가 설정되어 있는 것으로 간주
                            config['password_set'] = True
                except Exception as e:
                    print(f"⚠️ email_config.py 읽기 오류: {e}")
            
            # 현재 앱 설정에서도 확인
            current_password = app.config.get('MAIL_PASSWORD', '')
            if current_password and current_password != 'your-app-password':
                config['password_set'] = True
            
            return jsonify({
                'success': True,
                'config': config
            })
        except Exception as e:
            print(f"❌ 이메일 설정 조회 오류: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'설정 조회 중 오류가 발생했습니다: {str(e)}'
            }), 500
    
    elif request.method == 'POST':
        # 이메일 비밀번호 업데이트
        try:
            if request.is_json:
                mail_password = request.json.get('mail_password', '').strip()
            else:
                mail_password = request.form.get('mail_password', '').strip()
            
            if not mail_password:
                return jsonify({'success': False, 'error': '비밀번호를 입력해주세요.'}), 400
            
            # email_config.py 파일 경로
            email_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_config.py')
            
            # 파일이 없으면 생성
            if not os.path.exists(email_config_path):
                # 기본 email_config.py 파일 생성
                default_config = '''# -*- coding: utf-8 -*-
"""
이메일 설정 파일
네이버 메일 SMTP 설정을 관리합니다.

⚠️ 보안 주의사항:
- 이 파일은 .gitignore에 추가되어 있어야 합니다.
- 실제 비밀번호를 입력한 후 절대 공유하지 마세요.
"""

# 네이버 메일 SMTP 설정
MAIL_SERVER = 'smtp.naver.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'print7123@naver.com'

# ⚠️ 중요: 네이버 앱 비밀번호를 여기에 입력하세요
# 네이버 메일 → 환경설정 → 보안 → 2단계 인증 → 앱 비밀번호 생성
# 생성된 16자리 비밀번호를 아래에 입력하세요
MAIL_PASSWORD = 'your-app-password'  # 여기에 실제 앱 비밀번호 입력

# 설정 확인 함수
def is_password_set():
    """비밀번호가 실제로 설정되었는지 확인"""
    return MAIL_PASSWORD and MAIL_PASSWORD != 'your-app-password'
'''
                with open(email_config_path, 'w', encoding='utf-8') as f:
                    f.write(default_config)
            
            # email_config.py 파일 읽기
            with open(email_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # MAIL_PASSWORD 라인 찾아서 교체
            import re
            # 기존 MAIL_PASSWORD 라인 패턴
            pattern = r"MAIL_PASSWORD\s*=\s*['\"].*?['\"]"
            replacement = f"MAIL_PASSWORD = '{mail_password}'"
            
            if re.search(pattern, content):
                # 기존 라인 교체
                new_content = re.sub(pattern, replacement, content)
            else:
                # 라인이 없으면 추가
                new_content = content.replace(
                    "MAIL_PASSWORD = 'your-app-password'",
                    f"MAIL_PASSWORD = '{mail_password}'"
                )
            
            # 파일 쓰기
            with open(email_config_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # 앱 설정도 즉시 업데이트 (서버 재시작 전까지 임시)
            app.config['MAIL_PASSWORD'] = mail_password
            
            print("=" * 80)
            print("✅ 이메일 비밀번호가 저장되었습니다.")
            print(f"   파일: {email_config_path}")
            print("   ⚠️ 서버를 재시작하면 새로운 비밀번호가 적용됩니다.")
            print("=" * 80)
            
            return jsonify({
                'success': True,
                'message': '이메일 비밀번호가 저장되었습니다. 서버를 재시작하면 적용됩니다.'
            })
            
        except PermissionError:
            return jsonify({
                'success': False,
                'error': '파일 쓰기 권한이 없습니다. 관리자 권한으로 실행하거나 파일 권한을 확인하세요.'
            }), 500
        except Exception as e:
            print(f"❌ 이메일 비밀번호 저장 오류: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'비밀번호 저장 중 오류가 발생했습니다: {str(e)}'
            }), 500

@app.route('/api/admin/question/<int:question_id>/file', methods=['GET'])
@login_required
def download_question_file(question_id):
    """질문 첨부 파일 다운로드 또는 보기"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
    
    try:
        question = Question.query.get_or_404(question_id)
        
        if not question.file_path:
            return jsonify({'success': False, 'error': '첨부 파일이 없습니다.'}), 404
        
        # 파일 경로 구성
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], question.file_path)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다.'}), 404
        
        # 파일 확장자 확인
        file_ext = os.path.splitext(file_path)[1].lower()
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        
        # 원본 파일명 추출 (UUID 제거)
        # 파일 경로 형식: questions/{uuid}_{filename}
        if '/' in question.file_path:
            path_parts = question.file_path.split('/')
            filename_with_uuid = path_parts[-1]
            if '_' in filename_with_uuid:
                # UUID는 보통 32자리 hex이므로, 첫 번째 언더스코어 이후가 원본 파일명
                parts = filename_with_uuid.split('_', 1)
                if len(parts) > 1 and len(parts[0]) == 32:
                    original_filename = parts[1]
                else:
                    original_filename = filename_with_uuid
            else:
                original_filename = filename_with_uuid
        else:
            original_filename = os.path.basename(question.file_path)
        
        # 이미지 파일인 경우 미리보기, 그 외는 다운로드
        if file_ext in image_extensions:
            # 이미지 파일은 미리보기
            return send_file(file_path, mimetype=f'image/{file_ext[1:]}')
        else:
            # 그 외 파일은 다운로드
            return send_file(
                file_path,
                as_attachment=True,
                download_name=original_filename,
                mimetype='application/octet-stream'
            )
            
    except Exception as e:
        print(f"⚠️ 파일 다운로드 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '파일 다운로드 중 오류가 발생했습니다.'}), 500

@app.route('/api/admin/question/<int:question_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_question(question_id):
    """관리자가 질문 수정 또는 삭제"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
    
    try:
        question = Question.query.get_or_404(question_id)
        
        if request.method == 'DELETE':
            # 질문 삭제
            # 첨부 파일도 삭제
            if question.file_path:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], question.file_path)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"⚠️ 파일 삭제 실패: {e}")
            
            db.session.delete(question)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '질문이 성공적으로 삭제되었습니다.'
            })
        
        elif request.method == 'PUT':
            # 질문 수정
            if request.is_json:
                data = request.json
            else:
                data = request.form
            
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            is_public = data.get('is_public', True)
            
            if not title or not content:
                return jsonify({'success': False, 'error': '제목과 내용을 입력해주세요.'}), 400
            
            question.title = title
            question.content = content
            
            # is_public 설정
            try:
                if isinstance(is_public, str):
                    is_public = is_public.lower() == 'true'
                question.is_public = bool(is_public)
            except Exception:
                pass
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '질문이 성공적으로 수정되었습니다.',
                'question': {
                    'id': question.id,
                    'title': question.title,
                    'content': question.content,
                    'is_public': bool(question.is_public) if hasattr(question, 'is_public') else True
                }
            })
        
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ 질문 관리 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '질문 관리 중 오류가 발생했습니다.'}), 500

# 전역 에러 핸들러 추가 (모든 라우트 정의 후에 등록)
# 주의: error handler는 모든 라우트가 등록된 후에 정의되어야 함
@app.errorhandler(404)
def not_found_error(error):
    """404 오류 핸들러 - 모든 라우트 확인 후 실행"""
    # 요청된 URL 확인
    requested_url = request.path
    print(f"⚠️ 404 오류: 요청된 URL = {requested_url}")
    
    # 특정 라우트에 대한 디버깅 정보
    if '/admin/questions' in requested_url:
        print(f"⚠️ /admin/questions 라우트가 인식되지 않았습니다!")
        print(f"   등록된 라우트 목록:")
        with app.app_context():
            for rule in app.url_map.iter_rules():
                if 'admin' in str(rule) or 'question' in str(rule):
                    print(f"     - {rule}")
    
    try:
        return render_template('error.html', error_code=404, error_message='페이지를 찾을 수 없습니다.'), 404
    except Exception as e:
        print(f"⚠️ error.html 템플릿 렌더링 오류: {e}")
        return f"<h1>404 오류</h1><p>페이지를 찾을 수 없습니다.</p><p>요청 URL: {requested_url}</p>", 404

@app.errorhandler(500)
def internal_error(error):
    try:
        db.session.rollback()
        return render_template('error.html', error_code=500, error_message='서버 내부 오류가 발생했습니다.'), 500
    except:
        return f"<h1>500 오류</h1><p>서버 내부 오류가 발생했습니다.</p>", 500

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"⚠️ 처리되지 않은 예외: {e}")
    import traceback
    traceback.print_exc()
    try:
        db.session.rollback()
        return render_template('error.html', error_code=500, error_message=str(e)), 500
    except:
        return f"<h1>오류 발생</h1><p>{str(e)}</p>", 500

if __name__ == '__main__':
    try:
        with app.app_context():
            # 데이터베이스 생성 (안전하게)
            try:
                db.create_all()
                print("✅ 데이터베이스 초기화 완료")
            except Exception as e:
                print(f"⚠️ 데이터베이스 초기화 중 오류 (계속 진행): {e}")
            
            # 데이터베이스 스키마 업데이트 (기존 테이블에 컬럼 추가)
            try:
                from sqlalchemy import inspect, text
                inspector = inspect(db.engine)
                
                # service_category 테이블에 image_path 컬럼이 없으면 추가
                if 'service_category' in inspector.get_table_names():
                    columns = [col['name'] for col in inspector.get_columns('service_category')]
                    if 'image_path' not in columns:
                        print("📝 service_category 테이블에 image_path 컬럼 추가 중...")
                        db.session.execute(text('ALTER TABLE service_category ADD COLUMN image_path VARCHAR(500)'))
                        db.session.commit()
                        print("✅ image_path 컬럼 추가 완료")
                
                # question 테이블 스키마 업데이트 (중앙화된 함수 사용)
                update_question_schema()
                
                # board_category 테이블에 is_admin_only 컬럼이 없으면 추가
                if 'board_category' in inspector.get_table_names():
                    columns = [col['name'] for col in inspector.get_columns('board_category')]
                    if 'is_admin_only' not in columns:
                        print("📝 board_category 테이블에 is_admin_only 컬럼 추가 중...")
                        db.session.execute(text('ALTER TABLE board_category ADD COLUMN is_admin_only BOOLEAN DEFAULT 0'))
                        db.session.commit()
                        print("✅ is_admin_only 컬럼 추가 완료")
                        
                        # 기존 공지사항 카테고리를 관리자 전용으로 설정
                        notice_category = BoardCategory.query.filter_by(name='공지사항').first()
                        if notice_category:
                            notice_category.is_admin_only = True
                            db.session.commit()
                            print("✅ 공지사항 카테고리를 관리자 전용으로 설정 완료")
            except Exception as e:
                print(f"⚠️ 스키마 업데이트 중 오류 (무시 가능): {e}")
                try:
                    db.session.rollback()
                except:
                    pass
            
            # 기본 관리자 계정 생성 (없는 경우)
            try:
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    admin = User(
                        username='admin',
                        email='admin@onnuri.com',
                        password_hash=generate_password_hash('admin123'),
                        is_admin=True
                    )
                    db.session.add(admin)
                    db.session.commit()
                    print("✅ 기본 관리자 계정 생성: admin / admin123")
            except Exception as e:
                print(f"⚠️ 관리자 계정 생성 중 오류 (무시 가능): {e}")
                try:
                    db.session.rollback()
                except:
                    pass
            
            # 기본 서비스 카테고리 생성 (없는 경우)
            try:
                default_categories = [
                    {'name': 'coil_binding', 'display_name': '코일제본', 'icon': 'fas fa-link', 'color': 'primary', 'display_order': 1, 'description': '코일링을 통한 견고한 제본'},
                    {'name': 'wire_binding', 'display_name': '와이어링제본', 'icon': 'fas fa-link', 'color': 'success', 'display_order': 2, 'description': '와이어링을 통한 견고한 제본'},
                    {'name': 'perfect_binding', 'display_name': '무선제본', 'icon': 'fas fa-book', 'color': 'info', 'display_order': 3, 'description': '깔끔하고 세련된 무선 제본'},
                    {'name': 'saddle_binding', 'display_name': '중철제본', 'icon': 'fas fa-stapler', 'color': 'warning', 'display_order': 4, 'description': '전통적인 중철 방식의 제본'},
                    {'name': 'leaflet', 'display_name': '리플렛', 'icon': 'fas fa-file-alt', 'color': 'danger', 'display_order': 5, 'description': '리플렛 제작 서비스'},
                    {'name': 'brochure', 'display_name': '브로셔', 'icon': 'fas fa-book-open', 'color': 'secondary', 'display_order': 6, 'description': '브로셔 제작 서비스'},
                ]
                
                for cat_data in default_categories:
                    if not ServiceCategory.query.filter_by(name=cat_data['name']).first():
                        category = ServiceCategory(**cat_data)
                        db.session.add(category)
                
                db.session.commit()
                print("✅ 기본 서비스 카테고리 생성 완료")
            except Exception as e:
                print(f"⚠️ 서비스 카테고리 생성 중 오류 (무시 가능): {e}")
                try:
                    db.session.rollback()
                except:
                    pass
            
            # 기본 포트폴리오 카테고리 생성 (없는 경우)
            try:
                default_portfolio_categories = [
                    {'name': '전단지', 'display_order': 1},
                    {'name': '명함', 'display_order': 2},
                    {'name': '책자', 'display_order': 3},
                    {'name': '포스터', 'display_order': 4},
                    {'name': '브로슈어', 'display_order': 5},
                    {'name': '카탈로그', 'display_order': 6},
                    {'name': '기타', 'display_order': 7},
                ]
                
                for cat_data in default_portfolio_categories:
                    if not PortfolioCategory.query.filter_by(name=cat_data['name']).first():
                        category = PortfolioCategory(**cat_data)
                        db.session.add(category)
                
                db.session.commit()
                print("✅ 기본 포트폴리오 카테고리 생성 완료")
            except Exception as e:
                print(f"⚠️ 포트폴리오 카테고리 생성 중 오류 (무시 가능): {e}")
                try:
                    db.session.rollback()
                except:
                    pass
            
            # 기본 게시판 카테고리 생성 (없는 경우)
            try:
                if BoardCategory.query.count() == 0:
                    default_categories = [
                        {'name': '공지사항', 'description': '중요한 공지사항을 확인하세요', 'display_order': 1, 'is_admin_only': True},
                        {'name': '사용후기', 'description': '온누리인쇄나라 이용 후기를 남겨주세요', 'display_order': 2, 'is_admin_only': False}
                    ]
                    
                    for cat_data in default_categories:
                        if not BoardCategory.query.filter_by(name=cat_data['name']).first():
                            category = BoardCategory(**cat_data)
                            db.session.add(category)
                    
                    db.session.commit()
                    print("✅ 기본 게시판 카테고리 생성 완료")
            except Exception as e:
                print(f"⚠️ 게시판 카테고리 생성 중 오류 (무시 가능): {e}")
                try:
                    db.session.rollback()
                except:
                    pass
    except Exception as e:
        print(f"⚠️ 초기화 중 오류 발생 (서버는 계속 시작됩니다): {e}")
        import traceback
        traceback.print_exc()
    
    print("🚀 온누리인쇄나라 강화된 웹사이트를 시작합니다...")
    print("📱 브라우저에서 http://localhost:5000 으로 접속하세요.")
    print("👤 관리자 로그인: admin / admin123")
    print()
    print("=" * 60)
    print("서버가 정상적으로 시작되었습니다!")
    print("=" * 60)
    print()
    
    # 등록된 Q&A 엔드포인트 확인
    print("📋 등록된 Q&A 엔드포인트:")
    with app.app_context():
        # 모든 라우트 확인
        all_routes = [str(rule) for rule in app.url_map.iter_rules()]
        print(f"  📊 총 등록된 라우트 수: {len(all_routes)}")
        
        # Q&A 관련 라우트 확인
        routes = [str(rule) for rule in app.url_map.iter_rules() if 'question' in str(rule) or 'admin/questions' in str(rule)]
        if routes:
            print("  ✅ Q&A 관련 라우트:")
            for route in routes:
                print(f"     - {route}")
        else:
            print("  ⚠️ Q&A 엔드포인트가 등록되지 않았습니다!")
        
        # admin/questions 라우트 특별 확인
        admin_questions_routes = [str(rule) for rule in app.url_map.iter_rules() if '/admin/questions' in str(rule)]
        if admin_questions_routes:
            print(f"  ✅ 관리자 Q&A 페이지: {admin_questions_routes}")
        else:
            print("  ❌ /admin/questions 라우트가 등록되지 않았습니다!")
            print("  🔍 admin 관련 라우트 확인:")
            admin_routes = [str(rule) for rule in app.url_map.iter_rules() if 'admin' in str(rule)]
            for route in admin_routes[:10]:  # 최대 10개만 표시
                print(f"     - {route}")
    print()
    
    # 개발 모드 설정: 자동 리로드 및 템플릿 변경 감지
    # 템플릿 파일 변경 시 자동으로 감지하여 재시작
    template_files = []
    if os.path.exists(template_dir_abs):
        for root, dirs, files in os.walk(template_dir_abs):
            for file in files:
                if file.endswith(('.html', '.css', '.js')):
                    template_files.append(os.path.join(root, file))
    
    print(f"📁 자동 리로드 모니터링 파일: {len(template_files)}개")
    print("   - 템플릿 파일 변경 시 자동으로 반영됩니다")
    print("   - 브라우저에서 새로고침(F5)만 하면 최신 상태로 표시됩니다")
    print()
    
    # 배포 모드에 따른 서버 실행 설정
    if IS_PRODUCTION:
        # 프로덕션 모드: 디버그 비활성화, 보안 강화
        print("🚀 프로덕션 모드로 서버를 시작합니다...")
        print(f"   도메인: {DOMAIN}")
        print(f"   호스트: {HOST}")
        print(f"   포트: {PORT}")
        
        # 클라우드 환경 감지 (환경 변수 PORT가 설정되어 있으면 클라우드)
        cloud_port = os.environ.get('PORT')
        if cloud_port:
            PORT = int(cloud_port)
            print(f"   ☁️ 클라우드 환경 감지: 포트 {PORT} 사용")
        
        print("   ⚠️ 프로덕션 환경에서는 WSGI 서버(gunicorn, waitress 등) 사용을 권장합니다.")
        try:
            app.run(
                debug=False,  # 프로덕션에서는 디버그 비활성화
                host=HOST,
                port=PORT,
                use_reloader=False,  # 프로덕션에서는 자동 재시작 비활성화
                use_debugger=False,  # 디버거 비활성화
                threaded=True,  # 동시 요청 처리
            )
        except OSError as e:
            if "Address already in use" in str(e) or "포트가 이미 사용 중" in str(e):
                print(f"⚠️ 포트 {PORT}가 이미 사용 중입니다.")
                print("기존 서버를 종료하거나 다른 포트를 사용하세요.")
            else:
                print(f"❌ 서버 시작 오류: {e}")
            raise
    else:
        # 개발 모드: use_reloader=True로 설정하여 코드 변경 시 자동 재시작
        # extra_files로 템플릿 파일 변경도 감지
        # threaded=True로 설정하여 동시 요청 처리
        try:
            app.run(
                debug=True, 
                host=HOST, 
                port=PORT, 
                use_reloader=True,  # 코드 변경 시 자동 재시작
                use_debugger=True,  # 디버거 활성화
                threaded=True,     # 동시 요청 처리
                extra_files=template_files[:100] if template_files else None  # 템플릿 파일 변경 감지 (최대 100개)
            )
        except OSError as e:
            if "Address already in use" in str(e) or "포트가 이미 사용 중" in str(e):
                print(f"⚠️ 포트 {PORT}가 이미 사용 중입니다.")
                print("기존 서버를 종료하거나 다른 포트를 사용하세요.")
                print("포트 종료: taskkill /F /IM python.exe")
            else:
                print(f"❌ 서버 시작 오류: {e}")
            raise
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            import traceback
            traceback.print_exc()
            raise
