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
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'onnuri-print-enhanced-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///onnuri_print_enhanced.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PORTFOLIO_FOLDER'] = 'static/portfolio'
app.config['PORTFOLIO_THUMBNAILS'] = 'static/portfolio/thumbnails'
app.config['BROCHURE_FOLDER'] = 'static/brochures'
app.config['BROCHURE_THUMBNAILS'] = 'static/brochures/thumbnails'
app.config['SERVICE_IMAGE_FOLDER'] = 'static/service_images'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
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
app.config['MAIL_SERVER'] = 'smtp.naver.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'print7123@naver.com'
app.config['MAIL_PASSWORD'] = 'your-app-password'  # 실제 앱 비밀번호로 변경 필요

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PORTFOLIO_FOLDER'], exist_ok=True)
os.makedirs(app.config['PORTFOLIO_THUMBNAILS'], exist_ok=True)
os.makedirs(app.config['BROCHURE_FOLDER'], exist_ok=True)
os.makedirs(app.config['BROCHURE_THUMBNAILS'], exist_ok=True)
os.makedirs(app.config['SERVICE_IMAGE_FOLDER'], exist_ok=True)

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    is_answered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)

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
@login_required
def index():
    """강화된 메인 페이지 - 로그인 필수"""
    # 마케팅 통계 가져오기
    marketing_stats = get_marketing_stats()
    
    # 최근 작업 사례 가져오기
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(6).all()
    
    # 관리자 여부 확인
    is_admin = current_user.is_authenticated and current_user.is_admin
    
    # 포트폴리오 카테고리 가져오기
    portfolio_categories = PortfolioCategory.query.filter_by(is_active=True).order_by(PortfolioCategory.display_order, PortfolioCategory.name).all()
    
    # 서비스 카테고리 가져오기
    service_categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.display_order, ServiceCategory.name).all()
    
    return render_template('index.html', 
                         marketing_stats=marketing_stats,
                         recent_orders=recent_orders,
                         is_admin=is_admin,
                         portfolio_categories=portfolio_categories,
                         service_categories=service_categories)

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
        msg = MIMEMultipart('alternative')
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # 텍스트 버전
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # HTML 버전
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 이메일 발송
        context = ssl.create_default_context()
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls(context=context)
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"HTML 이메일 발송 오류: {e}")
        return False

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
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('사용자명과 비밀번호를 모두 입력해주세요.')
            return redirect(url_for('index'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=request.form.get('remember', False))
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('잘못된 사용자명 또는 비밀번호입니다.')
            return redirect(url_for('index'))
    
    return render_template('login.html')

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
    
    # 통계 정보
    portfolio_count = Portfolio.query.filter_by(is_active=True).count()
    brochure_count = Brochure.query.filter_by(is_active=True).count()
    order_count = Order.query.count()
    
    return render_template('admin_dashboard.html', 
                         portfolio_count=portfolio_count,
                         brochure_count=brochure_count,
                         order_count=order_count)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
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
        except Exception as e:
            print(f"⚠️ 스키마 업데이트 중 오류 (무시 가능): {e}")
            db.session.rollback()
        
        # 기본 관리자 계정 생성 (없는 경우)
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
        
        # 기본 서비스 카테고리 생성 (없는 경우)
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
        
        # 기본 포트폴리오 카테고리 생성 (없는 경우)
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
    
    print("🚀 온누리인쇄나라 강화된 웹사이트를 시작합니다...")
    print("📱 브라우저에서 http://localhost:5000 으로 접속하세요.")
    print("👤 관리자 로그인: admin / admin123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
