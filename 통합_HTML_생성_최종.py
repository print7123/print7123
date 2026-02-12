#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
홈페이지를 하나의 통합 HTML 파일로 생성하는 스크립트 (최종 개선 버전)
원본 http://localhost:5000/과 동일하게 작동하도록 모든 부분을 처리합니다.
"""

import os
import re
import base64

def read_file(filepath):
    """파일 읽기"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 파일 읽기 오류 ({filepath}): {e}")
        return None

def write_file(filepath, content):
    """파일 쓰기"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 파일 생성 완료: {filepath}")
        return True
    except Exception as e:
        print(f"❌ 파일 쓰기 오류 ({filepath}): {e}")
        return False

def encode_image_to_base64(image_path):
    """이미지를 base64로 인코딩"""
    try:
        if os.path.exists(image_path):
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                # 파일 확장자로 MIME 타입 결정
                ext = os.path.splitext(image_path)[1].lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                mime_type = mime_types.get(ext, 'image/jpeg')
                return f'data:{mime_type};base64,{img_base64}'
    except Exception as e:
        print(f"⚠️  이미지 인코딩 오류 ({image_path}): {e}")
    return None

def process_flask_templates(html_content, static_dir):
    """Flask 템플릿 문법을 정적 HTML로 변환"""
    print("   - Flask 템플릿 문법 처리 중...")
    
    # 1. 이미지 경로를 base64로 변환 (HTML 속성)
    # 정규식에서 따옴표 처리: 작은따옴표로 감싼 raw string에서 큰따옴표는 이스케이프 불필요
    image_pattern_html = r'src=["\']\{\{\s*url_for\(["\']static["\'],\s*filename=["\']images/([^"\']+)["\']\)\s*\}\}(\?v=[^"\']+)?["\']'
    
    def replace_image_html(match):
        filename = match.group(1)
        query_string = match.group(2) if match.group(2) else ''
        image_path = os.path.join(static_dir, 'images', filename)
        base64_data = encode_image_to_base64(image_path)
        if base64_data:
            print(f"      ✅ 이미지 인코딩 (HTML): {filename}")
            return f'src="{base64_data}"'
        return f'src="/static/images/{filename}{query_string}"'
    
    html_content = re.sub(image_pattern_html, replace_image_html, html_content)
    
    # 2. JavaScript 문자열 내부의 이미지 경로 처리 (배열 내부 포함)
    # '{{ url_for("static", filename="images/main_header.jpg") }}?v=20260211' 형식
    image_pattern_js = r'\{\{\s*url_for\(["\']static["\'],\s*filename=["\']images/([^"\']+)["\']\)\s*\}\}(\?v=[^"\']+)?'
    
    def replace_image_js(match):
        filename = match.group(1)
        query_string = match.group(2) if match.group(2) else ''
        image_path = os.path.join(static_dir, 'images', filename)
        base64_data = encode_image_to_base64(image_path)
        if base64_data:
            print(f"      ✅ 이미지 인코딩 (JS): {filename}")
            return f"'{base64_data}'"
        return f"'/static/images/{filename}{query_string}'"
    
    html_content = re.sub(image_pattern_js, replace_image_js, html_content)
    
    # 3. 나머지 url_for() 함수 처리
    html_content = re.sub(
        r'\{\{\s*url_for\(["\']static["\'],\s*filename=["\']([^"\']+)["\']\)\s*\}\}',
        r'/static/\1',
        html_content
    )
    
    # 4. 라우트 url_for() 처리
    routes = {
        r'\{\{\s*url_for\(["\']board["\']\)\s*\}\}': '/board',
        r'\{\{\s*url_for\(["\']board_detail["\'],\s*post_id=([^\)]+)\)\s*\}\}': r'/board/\1',
        r'\{\{\s*url_for\(["\']admin_dashboard["\']\)\s*\}\}': '/admin/dashboard',
        r'\{\{\s*url_for\(["\']login["\']\)\s*\}\}': '/login',
        r'\{\{\s*url_for\(["\']logout["\']\)\s*\}\}': '/logout',
    }
    for pattern, replacement in routes.items():
        html_content = re.sub(pattern, replacement, html_content)
    
    # 5. 변수 대체
    html_content = re.sub(r'\{\{\s*is_admin\s*\}\}', 'false', html_content)
    html_content = re.sub(r'\{\{\s*is_authenticated\s*\}\}', 'false', html_content)
    
    # 6. {% if not is_admin %} ... {% else %} ... {% endif %} 처리
    # 견적 계산기 보호 메시지 div는 제거 (일반 사용자도 견적 계산 가능)
    # 하지만 JavaScript 내부의 {% if not is_admin %}는 나중에 처리
    html_content = re.sub(
        r'\{%\s*if\s+not\s+is_admin\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}',
        '',  # 보호 메시지 제거 (일반 사용자도 견적 계산 가능)
        html_content,
        flags=re.DOTALL
    )
    
    # 7. {% if is_admin %} ... {% endif %} 처리 (제거)
    html_content = re.sub(
        r'\{%\s*if\s+is_admin\s*%\}.*?\{%\s*endif\s*%\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # 8. {% if is_authenticated %} ... {% else %} ... {% endif %} 처리
    html_content = re.sub(
        r'\{%\s*if\s+is_authenticated\s*%\}.*?\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}',
        r'\1',  # 로그인하지 않은 경우의 내용만 유지
        html_content,
        flags=re.DOTALL
    )
    
    # 9. portfolio_categories 처리
    portfolio_html = """
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('전단지')">전단지</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('명함')">명함</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('책자')">책자</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('포스터')">포스터</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('브로슈어')">브로슈어</button>
"""
    html_content = re.sub(
        r'\{%\s*if\s+portfolio_categories\s*%\}.*?\{%\s*endif\s*%\}',
        portfolio_html,
        html_content,
        flags=re.DOTALL
    )
    
    # 10. recent_posts 처리
    empty_posts = '''<div class="p-3 text-center text-muted">
                            <i class="fas fa-box-open fa-2x mb-2"></i>
                            <p>아직 등록된 게시글이 없습니다.</p>
                        </div>'''
    html_content = re.sub(
        r'\{%\s*if\s+recent_posts\s*%\}.*?\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}',
        empty_posts,
        html_content,
        flags=re.DOTALL
    )
    
    # 11. for 루프 제거 (recent_posts, portfolio_categories)
    html_content = re.sub(
        r'\{%\s*for\s+post\s+in\s+recent_posts\s*%\}.*?\{%\s*endfor\s*%\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    html_content = re.sub(
        r'\{%\s*for\s+category\s+in\s+portfolio_categories\s*%\}.*?\{%\s*endfor\s*%\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # 12. 기타 변수 제거 (복잡한 표현식 포함)
    # post.created_at.strftime() 같은 복잡한 표현식 처리
    html_content = re.sub(
        r'\{\{\s*post\.created_at\.strftime\([^\)]+\)\s*if\s+post\.created_at\s+else\s+[\'"]\s*[\'"]\s*\}\}',
        '',
        html_content
    )
    # post.content[:100] 슬라이싱 처리
    html_content = re.sub(
        r'\{\{\s*post\.content\[:100\]\s*\}\}',
        '',
        html_content
    )
    # {% if post.content|length > 100 %}...{% endif %} 처리
    html_content = re.sub(
        r'\{%\s*if\s+post\.content\|length\s*>\s*100\s*%\}[^%]*\{%\s*endif\s*%\}',
        '',
        html_content
    )
    # {{ post.content[:100] }}{% if post.content|length > 100 %}...{% endif %} 패턴 처리
    html_content = re.sub(
        r'\{\{\s*post\.content\[:100\]\s*\}\}\{%\s*if\s+post\.content\|length\s*>\s*100\s*%\}[^%]*\{%\s*endif\s*%\}',
        '',
        html_content
    )
    # {% if loop.last %} 처리
    html_content = re.sub(
        r'\{%\s*if\s+loop\.last\s*%\}[^%]*\{%\s*endif\s*%\}',
        '',
        html_content
    )
    # {% if post.is_pinned %}, {% if post.is_notice %}, {% if post.file_path %} 처리
    html_content = re.sub(
        r'\{%\s*if\s+post\.(is_pinned|is_notice|file_path)\s*%\}.*?\{%\s*endif\s*%\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # 단순 변수들 제거
    post_vars = ['post.title', 'post.content', 'post.author_name', 'post.view_count', 
                 'post.id', 'post.is_pinned', 'post.is_notice', 
                 'post.file_path', 'loop.last', 'category.name']
    for var in post_vars:
        html_content = re.sub(r'\{\{\s*' + re.escape(var) + r'\s*\}\}', '', html_content)
    
    # 13. JavaScript 내부의 Jinja2 처리
    html_content = re.sub(
        r'const\s+is_admin\s*=\s*\{%\s*if\s+is_admin\s*%\}true\{%\s*else\s*%\}false\{%\s*endif\s*%\};',
        'const is_admin = false;',
        html_content
    )
    
    # 13-1. JavaScript 내부의 {% if not is_admin %} 블록 제거 (개발자 도구 방지 코드 제거)
    # 이 블록은 견적 계산기 보호를 위한 것이므로 통합 HTML에서는 제거
    html_content = re.sub(
        r'\{%\s*if\s+not\s+is_admin\s*%\}(.*?)\{%\s*endif\s*%\}',
        '',  # 개발자 도구 방지 코드 제거
        html_content,
        flags=re.DOTALL
    )
    
    # 14. Q&A 섹션 API 호출 처리 (file:// 프로토콜 감지)
    # loadQuestions 함수에서 fetch 호출 전에 file:// 체크 추가
    # questionList 체크 후, 리셋 모드 체크 전에 file:// 체크 삽입
    qa_check_pattern = r'(const questionList = document\.getElementById\([\'"]questionList[\'"]\);\s*if \(!questionList\) \{[^}]+\}return;\s*\}\s*)(// 리셋 모드일 때는 기존 내용 초기화)'
    
    def add_qa_file_check(match):
        before = match.group(1)
        after = match.group(2)
        return before + '''// file:// 프로토콜 또는 서버가 없는 경우 처리
            if (window.location.protocol === 'file:' || !window.location.hostname) {
                questionList.innerHTML = `
                    <div class="text-center text-muted py-3">
                        <i class="fas fa-inbox fa-2x mb-2"></i>
                        <p>Q&A는 서버가 실행 중일 때만 표시됩니다.</p>
                        <p class="text-muted small">통합 HTML 파일에서는 Q&A를 볼 수 없습니다.</p>
                    </div>
                `;
                isFetchingQuestions = false;
                return;
            }
            
            ''' + after
    
    html_content = re.sub(qa_check_pattern, add_qa_file_check, html_content, flags=re.DOTALL)
    
    # Q&A 폼 제출도 file:// 체크 추가
    qa_form_pattern = r'(questionForm\.addEventListener\([\'"]submit[\'"],\s*async function\(e\)\s*\{[^}]*e\.preventDefault\(\);[^}]*const formData = new FormData\(questionForm\);)'
    
    def add_qa_form_check(match):
        before = match.group(1)
        return before + '''
                    // file:// 프로토콜 체크
                    if (window.location.protocol === 'file:' || !window.location.hostname) {
                        alert('Q&A 질문 등록은 서버가 실행 중일 때만 가능합니다.');
                        return;
                    }
                    '''
    
    html_content = re.sub(qa_form_pattern, add_qa_form_check, html_content, flags=re.DOTALL)
    
    # 15. 게시판 링크 처리 (file:// 프로토콜 감지)
    # /board 링크를 클릭했을 때 file:// 프로토콜 체크
    board_link_pattern = r'href=["\']/board["\']'
    
    def replace_board_link(match):
        return 'href="/board" onclick="if (window.location.protocol === \'file:\' || !window.location.hostname) { event.preventDefault(); alert(\'게시판은 서버가 실행 중일 때만 접근할 수 있습니다.\\n\\n서버를 실행하려면 \\\'🚀_서버_시작_최종분.bat\\\' 파일을 실행하세요.\'); return false; }"'
    
    html_content = re.sub(board_link_pattern, replace_board_link, html_content)
    
    # 게시판 전체 보기 버튼도 처리
    board_button_pattern = r'href=["\']\{\{\s*url_for\(["\']board["\']\)\s*\}\}["\']'
    html_content = re.sub(
        board_button_pattern,
        'href="/board" onclick="if (window.location.protocol === \'file:\' || !window.location.hostname) { event.preventDefault(); alert(\'게시판은 서버가 실행 중일 때만 접근할 수 있습니다.\'); return false; }"',
        html_content
    )
    
    # 게시판 상세 링크도 처리
    board_detail_pattern = r'href=["\']\{\{\s*url_for\(["\']board_detail["\'],\s*post_id=([^\)]+)\)\s*\}\}["\']'
    html_content = re.sub(
        board_detail_pattern,
        r'href="/board/\1" onclick="if (window.location.protocol === \'file:\' || !window.location.hostname) { event.preventDefault(); alert(\'게시판은 서버가 실행 중일 때만 접근할 수 있습니다.\'); return false; }"',
        html_content
    )
    
    # 16. 남은 모든 Jinja2 문법 제거
    html_content = re.sub(r'\{%[^%]*%\}', '', html_content)
    html_content = re.sub(r'\{\{[^}]*\}\}', '', html_content)
    
    return html_content

def process_javascript(js_content, static_dir):
    """JavaScript 코드 개선"""
    if not js_content:
        return js_content
    
    print("   - JavaScript 코드 개선 중...")
    
    # JavaScript 내부의 이미지 경로를 base64로 변환
    # 정규식에서 따옴표 처리: 큰따옴표로 감싼 raw string에서 작은따옴표는 이스케이프 불필요
    image_pattern = r"'\{\{\s*url_for\(['\"]static['\"],\s*filename=['\"]images/([^'\"]+)['\"]\)\s*\}\}(\?v=[^'\"]+)?'"
    
    def replace_js_img(match):
        filename = match.group(1)
        query_string = match.group(2) if match.group(2) else ''
        image_path = os.path.join(static_dir, 'images', filename)
        base64_data = encode_image_to_base64(image_path)
        if base64_data:
            print(f"      ✅ 이미지 인코딩 (JS): {filename}")
            return f"'{base64_data}'"
        return f"'/static/images/{filename}{query_string}'"
    
    js_content = re.sub(image_pattern, replace_js_img, js_content)
    
    # protectQuoteForm 함수 비활성화 (통합 HTML에서는 보호 기능 불필요)
    # 함수 전체를 비활성화
    js_content = re.sub(
        r'function\s+protectQuoteForm\(\)\s*\{',
        'function protectQuoteForm() {\n    // 통합 HTML에서는 보호 기능 비활성화\n    return;',
        js_content
    )
    
    # protectQuoteForm 호출 제거 또는 비활성화
    js_content = re.sub(
        r'protectQuoteForm\(\);',
        '// protectQuoteForm(); // 통합 HTML에서는 비활성화',
        js_content
    )
    
    # alert 메시지 제거 (견적 계산 영역 보호 관련)
    js_content = re.sub(
        r"alert\(['\"]견적 계산 영역은 보호되어 있습니다[^'\"]*['\"]\);",
        '// alert 제거 (통합 HTML)',
        js_content
    )
    
    # 포트폴리오 로딩 오류 처리
    js_content = re.sub(
        r'async function loadPortfolio\([^)]*\)\s*\{[^}]*const response = await fetch\(`/portfolio\?category=\$\{category\}`\);',
        '''async function loadPortfolio(category = 'all', reset = false) {
    if (reset) {
        portfolioPage = 0;
        currentCategory = category;
    }
    const portfolioGrid = document.getElementById('portfolioGrid');
    if (!portfolioGrid) return;
    if (window.location.protocol === 'file:' || !window.location.hostname) {
        portfolioGrid.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-images fa-3x text-muted mb-3"></i>
                <p class="text-muted">포트폴리오는 서버가 실행 중일 때만 표시됩니다.</p>
                <p class="text-muted small">통합 HTML 파일에서는 포트폴리오를 볼 수 없습니다.</p>
            </div>
        `;
        return;
    }
    try {
        const response = await fetch(`/portfolio?category=${category}`);''',
        js_content,
        flags=re.DOTALL
    )
    
    # 견적 계산 API 호출 처리 (file:// 프로토콜 감지 및 클라이언트 사이드 계산)
    # handleQuoteCalculation 함수에서 fetch 호출 전에 file:// 체크 추가
    # fetch('/quote' 호출 바로 앞에 체크 추가
    quote_calc_pattern = r'(// 견적 계산 API 호출\s*fetch\([\'"]/quote[\'"],)'
    
    def add_quote_calc_check(match):
        before = match.group(1)
        return '''// file:// 프로토콜 체크 - 클라이언트 사이드 계산
    if (window.location.protocol === 'file:' || !window.location.hostname) {
        try {
            const result = calculateQuoteClientSide(formData);
            if (result && result.success) {
                displayQuoteResult(result, formData);
            } else {
                showAlert('견적 계산 중 오류가 발생했습니다.', 'danger');
            }
        } catch (error) {
            console.error('클라이언트 사이드 계산 오류:', error);
            showAlert('견적 계산 중 오류가 발생했습니다: ' + error.message, 'danger');
        }
        
        // 버튼 상태 복원
        calculateBtn.innerHTML = originalText;
        calculateBtn.disabled = false;
        window.isCalculating = false;
        return;
    }
    
    // 서버가 있는 경우 API 호출
    ''' + before
    
    js_content = re.sub(quote_calc_pattern, add_quote_calc_check, js_content, flags=re.DOTALL)
    
    # 클라이언트 사이드 견적 계산 함수 추가
    client_side_calc = '''
// 클라이언트 사이드 견적 계산 함수 (통합 HTML용) - 서버 로직과 동일
function calculateQuoteClientSide(formData) {
    // 한글 값을 서버 형식으로 변환
    const printTypeMap = {
        '흑백': 'black_white',
        '컬러': 'laser_color',
        '레이져칼라': 'laser_color',
        '잉크칼라': 'ink_color'
    };
    
    const printMethodMap = {
        '단면': 'single',
        '양면': 'double'
    };
    
    const bindingTypeMap = {
        '링제본': 'ring',
        '무선제본': 'perfect',
        '중철제본': 'saddle',
        '접지제본': 'folding'
    };
    
    // 값 변환 (한글 값이면 변환, 이미 서버 형식이면 그대로 사용)
    let printType = printTypeMap[formData.printType] || formData.printType || 'black_white';
    let printMethod = printMethodMap[formData.printMethod] || formData.printMethod || 'single';
    let bindingType = bindingTypeMap[formData.bindingType] || formData.bindingType || 'ring';
    const pages = parseInt(formData.pages) || 1;
    const quantity = parseInt(formData.quantity) || 1;
    
    // 서버 형식이 아닌 경우 기본값으로 설정
    if (!['black_white', 'laser_color', 'ink_color'].includes(printType)) {
        printType = 'black_white';
    }
    if (!['single', 'double'].includes(printMethod)) {
        printMethod = 'single';
    }
    if (!['ring', 'perfect', 'saddle', 'folding'].includes(bindingType)) {
        bindingType = 'ring';
    }
    
    // 페이지 수에 따른 출력 가격 계산 (서버 로직과 동일)
    function getPrintPrice(printType, totalPages, printMethod) {
        let priceRanges;
        
        if (totalPages <= 500) {
            priceRanges = {
                'black_white': {'single': 40, 'double': 40},
                'laser_color': {'single': 150, 'double': 150},
                'ink_color': {'single': 70, 'double': 70}
            };
        } else if (totalPages <= 5000) {
            priceRanges = {
                'black_white': {'single': 38, 'double': 33},
                'laser_color': {'single': 115, 'double': 110},
                'ink_color': {'single': 66, 'double': 60}
            };
        } else if (totalPages <= 10000) {
            priceRanges = {
                'black_white': {'single': 30, 'double': 25},
                'laser_color': {'single': 93, 'double': 88},
                'ink_color': {'single': 55, 'double': 50}
            };
        } else if (totalPages <= 15000) {
            priceRanges = {
                'black_white': {'single': 27, 'double': 22},
                'laser_color': {'single': 82, 'double': 77},
                'ink_color': {'single': 50, 'double': 45}
            };
        } else {
            priceRanges = {
                'black_white': {'single': 25, 'double': 20},
                'laser_color': {'single': 72, 'double': 66},
                'ink_color': {'single': 45, 'double': 40}
            };
        }
        
        return priceRanges[printType] ? (priceRanges[printType][printMethod] || 40) : 40;
    }
    
    // 수량에 따른 제본 가격 계산 (서버 로직과 동일)
    function getBindingPrice(bindingType, quantity) {
        if (bindingType === 'ring') {
            if (quantity <= 30) return 2200;
            else if (quantity <= 49) return 1650;
            else if (quantity <= 99) return 1430;
            else return 1100;
        } else if (bindingType === 'perfect') {
            if (quantity <= 30) return 2200;
            else if (quantity <= 49) return 1100;
            else if (quantity <= 99) return 770;
            else return 770;
        } else if (bindingType === 'saddle') {
            return 330;
        } else if (bindingType === 'folding') {
            return 500;
        }
        return 0;
    }
    
    // 총 페이지 수 계산
    const totalPages = pages * quantity;
    
    // 출력 가격 계산
    const unitPrintPrice = getPrintPrice(printType, totalPages, printMethod);
    const totalPrintPrice = unitPrintPrice * totalPages;
    
    // 제본 가격 계산
    const unitBindingPrice = getBindingPrice(bindingType, quantity);
    const totalBindingPrice = unitBindingPrice * quantity;
    
    // 총 가격 (출력비 + 제본비) - 부가세 포함
    const totalPriceWithTax = totalPrintPrice + totalBindingPrice;
    
    // 세액 계산 (부가세 10%)
    const taxAmount = Math.round(totalPriceWithTax * 0.1);
    
    // 총 가격 (부가세 제외)
    const totalPriceWithoutTax = totalPriceWithTax - taxAmount;
    
    // 단위 가격 (부가세 제외)
    const unitPrice = totalPriceWithoutTax / quantity;
    
    return {
        success: true,
        unit_price: Math.round(unitPrice * 100) / 100,
        total_price: totalPriceWithoutTax,
        total_price_with_tax: totalPriceWithTax,
        tax_amount: taxAmount,
        discount_rate: 0,
        print_price: totalPrintPrice,
        binding_price: totalBindingPrice,
        unit_print_price: unitPrintPrice,
        unit_binding_price: unitBindingPrice,
        pages: pages,
        total_pages: totalPages
    };
}
'''
    
    # 클라이언트 사이드 계산 함수를 handleQuoteCalculation 함수 앞에 추가
    # displayQuoteResult 함수도 안전하게 수정
    js_content = re.sub(
        r'(// 견적 계산 처리 \(버튼 클릭 이벤트용\)\s*function handleQuoteCalculation)',
        client_side_calc + r'\n\n\1',
        js_content
    )
    
    # displayQuoteResult 함수의 toLocaleString 호출을 안전하게 수정
    # undefined 체크 추가
    js_content = re.sub(
        r'if \(unitPrintPriceEl\) unitPrintPriceEl\.textContent = data\.unit_print_price\.toLocaleString\(\);',
        'if (unitPrintPriceEl && data.unit_print_price != null) unitPrintPriceEl.textContent = Number(data.unit_print_price).toLocaleString();',
        js_content
    )
    js_content = re.sub(
        r'if \(printPriceEl\) printPriceEl\.textContent = data\.print_price\.toLocaleString\(\);',
        'if (printPriceEl && data.print_price != null) printPriceEl.textContent = Number(data.print_price).toLocaleString();',
        js_content
    )
    js_content = re.sub(
        r'if \(bindingPriceEl\) bindingPriceEl\.textContent = data\.unit_binding_price\.toLocaleString\(\);',
        'if (bindingPriceEl && data.unit_binding_price != null) bindingPriceEl.textContent = Number(data.unit_binding_price).toLocaleString();',
        js_content
    )
    js_content = re.sub(
        r'if \(totalBindingPriceEl\) totalBindingPriceEl\.textContent = data\.binding_price\.toLocaleString\(\);',
        'if (totalBindingPriceEl && data.binding_price != null) totalBindingPriceEl.textContent = Number(data.binding_price).toLocaleString();',
        js_content
    )
    js_content = re.sub(
        r'if \(unitPriceEl\) unitPriceEl\.textContent = data\.unit_price\.toLocaleString\(\);',
        'if (unitPriceEl && data.unit_price != null) unitPriceEl.textContent = Number(data.unit_price).toLocaleString();',
        js_content
    )
    js_content = re.sub(
        r'if \(totalPriceEl\) totalPriceEl\.textContent = data\.total_price_with_tax\.toLocaleString\(\);',
        'if (totalPriceEl && data.total_price_with_tax != null) totalPriceEl.textContent = Number(data.total_price_with_tax).toLocaleString();',
        js_content
    )
    js_content = re.sub(
        r'totalPagesElement\.textContent = data\.total_pages\.toLocaleString\(\);',
        'totalPagesElement.textContent = (data.total_pages != null) ? Number(data.total_pages).toLocaleString() : \'\';',
        js_content
    )
    
    js_content = re.sub(
        r'catch\s*\(error\)\s*\{[^}]*포트폴리오를 불러오는 중 오류가 발생했습니다[^}]*\}',
        '''catch (error) {
                console.error('포트폴리오 로딩 오류:', error);
                portfolioGrid.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-images fa-3x text-muted mb-3"></i>
                        <p class="text-muted">포트폴리오는 서버가 실행 중일 때만 표시됩니다.</p>
                    </div>
                `;
            }''',
        js_content,
        flags=re.DOTALL
    )
    
    return js_content

def create_integrated_html():
    """통합 HTML 파일 생성"""
    script_path = os.path.abspath(__file__)
    base_dir = os.path.dirname(script_path)
    templates_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    print("=" * 60)
    print("통합 HTML 파일 생성 (최종 개선 버전)")
    print("=" * 60)
    
    index_html_path = os.path.join(templates_dir, 'index.html')
    style_css_path = os.path.join(static_dir, 'css', 'style.css')
    main_js_path = os.path.join(static_dir, 'js', 'main.js')
    clean_preview_js_path = os.path.join(static_dir, 'js', 'clean_preview.js')
    output_path = os.path.join(base_dir, 'index_통합.html')
    
    # 파일 읽기
    print("\n[1/5] 파일 읽는 중...")
    index_html = read_file(index_html_path)
    if not index_html:
        return False
    
    style_css = read_file(style_css_path) or ""
    main_js = read_file(main_js_path) or ""
    clean_preview_js = read_file(clean_preview_js_path) or ""
    
    print(f"   ✅ index.html: {len(index_html):,} 문자")
    print(f"   ✅ style.css: {len(style_css):,} 문자")
    print(f"   ✅ main.js: {len(main_js):,} 문자")
    print(f"   ✅ clean_preview.js: {len(clean_preview_js):,} 문자")
    
    # 통합 처리
    print("\n[2/5] CSS 링크 제거 중...")
    index_html = re.sub(
        r'<link[^>]*href=["\']\{\{.*?url_for.*?style\.css.*?\}\}["\'][^>]*>',
        '',
        index_html
    )
    
    print("[3/5] Flask 템플릿 문법 처리 중...")
    index_html = process_flask_templates(index_html, static_dir)
    
    print("[4/5] CSS/JS 통합 중...")
    if style_css:
        index_html = re.sub(
            r'(</style>)',
            f'\n        /* ========== style.css ========== */\n        {style_css}\n    \\1',
            index_html,
            count=1
        )
    
    # 외부 JS 파일 참조 제거
    index_html = re.sub(
        r'<script\s+src=["\']\{\{.*?main\.js.*?\}\}["\'][^>]*></script>',
        '',
        index_html
    )
    index_html = re.sub(
        r'<script\s+src=["\']\{\{.*?clean_preview\.js.*?\}\}["\'][^>]*></script>',
        '',
        index_html
    )
    
    # JavaScript 처리 및 추가
    main_js = process_javascript(main_js, static_dir)
    js_content = ""
    if main_js:
        js_content += f'\n    <!-- ========== main.js ========== -->\n    <script>\n{main_js}\n    </script>'
    if clean_preview_js:
        js_content += f'\n    <!-- ========== clean_preview.js ========== -->\n    <script>\n{clean_preview_js}\n    </script>'
    
    if js_content:
        index_html = re.sub(r'(</body>)', f'{js_content}\\1', index_html, count=1)
    
    # 최종 검증 및 정리
    print("[5/5] 최종 검증 및 정리 중...")
    
    # 남은 Jinja2 문법 확인
    remaining = re.findall(r'\{%[^%]*%\}|\{\{[^}]*\}\}', index_html)
    if remaining:
        print(f"⚠️  경고: {len(remaining)}개의 Jinja2 문법이 남아있습니다.")
        for i, jinja in enumerate(remaining[:10]):  # 처음 10개 표시
            print(f"      {i+1}. {jinja[:80]}")
        
        # 강제로 남은 Jinja2 문법 제거
        print("   - 남은 Jinja2 문법 강제 제거 중...")
        index_html = re.sub(r'\{%[^%]*%\}', '', index_html)
        index_html = re.sub(r'\{\{[^}]*\}\}', '', index_html)
    else:
        print("   ✅ 모든 Jinja2 문법이 처리되었습니다.")
    
    # 빈 줄 정리 (3개 이상 연속된 빈 줄을 2개로)
    index_html = re.sub(r'\n\s*\n\s*\n+', '\n\n', index_html)
    
    # 파일 저장
    if write_file(output_path, index_html):
        print("\n" + "=" * 60)
        print("✅ 통합 HTML 파일 생성 완료!")
        print(f"📁 파일: {output_path}")
        print(f"📊 크기: {len(index_html):,} 문자 ({len(index_html)/1024:.1f} KB)")
        print("=" * 60)
        print("\n💡 사용 방법:")
        print("   1. 생성된 'index_통합.html' 파일을 브라우저에서 직접 열 수 있습니다.")
        print("   2. 서버 없이도 작동하지만, 포트폴리오는 서버가 필요합니다.")
        print("   3. 모든 이미지와 CSS/JS가 파일에 포함되어 있습니다.")
        print("=" * 60)
        return True
    return False

if __name__ == "__main__":
    create_integrated_html()

