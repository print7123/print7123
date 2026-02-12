#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
홈페이지를 하나의 통합 HTML 파일로 생성하는 스크립트 (개선 버전)
외부 CSS, JS 파일을 모두 인라인으로 포함하고 모든 Flask 템플릿 문법을 처리합니다.
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
    
    # 1. url_for() 함수를 실제 경로로 대체 (이미지는 base64로 변환)
    # 먼저 이미지 경로를 찾아서 base64로 변환 (HTML과 JavaScript 모두)
    # HTML 속성 내부의 이미지
    image_pattern_html = r'src=["\']\{\{\s*url_for\([\'"]static[\'"],\s*filename=[\'"]images/([^\'"]+)[\'"]\)\s*\}\}["\']'
    
    def replace_image_path_html(match):
        filename = match.group(1)
        image_path = os.path.join(static_dir, 'images', filename)
        base64_data = encode_image_to_base64(image_path)
        if base64_data:
            print(f"      ✅ 이미지 인코딩 (HTML): {filename}")
            return f'src="{base64_data}"'
        else:
            print(f"      ⚠️  이미지 인코딩 실패: {filename}, 경로 사용")
            return f'src="/static/images/{filename}"'
    
    html_content = re.sub(image_pattern_html, replace_image_path_html, html_content)
    
    # JavaScript 문자열 내부의 이미지 (따옴표 포함, 쿼리 스트링 포함)
    # '{{ url_for("static", filename="images/main_header.jpg") }}?v=20260211' 형식 처리
    image_pattern_js = r'\{\{\s*url_for\([\'"]static[\'"],\s*filename=[\'"]images/([^\'"]+)[\'"]\)\s*\}\}(\?v=[^\'"]+)?'
    
    def replace_image_path_js(match):
        filename = match.group(1)
        query_string = match.group(2) if match.group(2) else ''
        image_path = os.path.join(static_dir, 'images', filename)
        base64_data = encode_image_to_base64(image_path)
        if base64_data:
            print(f"      ✅ 이미지 인코딩 (JS): {filename}")
            return f"'{base64_data}'"
        else:
            print(f"      ⚠️  이미지 인코딩 실패: {filename}, 경로 사용")
            return f"'/static/images/{filename}{query_string}'"
    
    html_content = re.sub(image_pattern_js, replace_image_path_js, html_content)
    
    # 나머지 url_for() 함수를 실제 경로로 대체
    html_content = re.sub(
        r'\{\{\s*url_for\([\'"]static[\'"],\s*filename=[\'"]([^\'"]+)[\'"]\)\s*\}\}',
        r'/static/\1',
        html_content
    )
    
    # url_for('board'), url_for('board_detail', ...) 등 라우트 처리
    html_content = re.sub(
        r'\{\{\s*url_for\([\'"]board[\'"]\)\s*\}\}',
        '/board',
        html_content
    )
    html_content = re.sub(
        r'\{\{\s*url_for\([\'"]board_detail[\'"],\s*post_id=([^\)]+)\)\s*\}\}',
        r'/board/\1',
        html_content
    )
    html_content = re.sub(
        r'\{\{\s*url_for\([\'"]admin_dashboard[\'"]\)\s*\}\}',
        '/admin/dashboard',
        html_content
    )
    html_content = re.sub(
        r'\{\{\s*url_for\([\'"]login[\'"]\)\s*\}\}',
        '/login',
        html_content
    )
    html_content = re.sub(
        r'\{\{\s*url_for\([\'"]logout[\'"]\)\s*\}\}',
        '/logout',
        html_content
    )
    
    # 2. 변수 대체
    html_content = re.sub(r'\{\{\s*is_admin\s*\}\}', 'false', html_content)
    html_content = re.sub(r'\{\{\s*is_authenticated\s*\}\}', 'false', html_content)
    
    # 3. {% if not is_admin %} ... {% else %} ... {% endif %} 처리
    # 견적 계산기 보호 메시지
    html_content = re.sub(
        r'\{%\s*if\s+not\s+is_admin\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}',
        r'\1',
        html_content,
        flags=re.DOTALL
    )
    
    # 4. {% if is_admin %} ... {% endif %} 처리 (제거)
    html_content = re.sub(
        r'\{%\s*if\s+is_admin\s*%\}.*?\{%\s*endif\s*%\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # 5. {% if is_authenticated %} ... {% else %} ... {% endif %} 처리
    # 로그인 버튼으로 대체
    html_content = re.sub(
        r'\{%\s*if\s+is_authenticated\s*%\}.*?\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}',
        r'\1',
        html_content,
        flags=re.DOTALL
    )
    
    # 6. {% if portfolio_categories %} ... {% endif %} 처리
    portfolio_categories_html = """
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('전단지')">전단지</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('명함')">명함</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('책자')">책자</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('포스터')">포스터</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('브로슈어')">브로슈어</button>
"""
    html_content = re.sub(
        r'\{%\s*if\s+portfolio_categories\s*%\}.*?\{%\s*endif\s*%\}',
        portfolio_categories_html,
        html_content,
        flags=re.DOTALL
    )
    
    # 7. {% if recent_posts %} ... {% else %} ... {% endif %} 처리
    empty_posts_html = '''<div class="p-3 text-center text-muted">
                            <i class="fas fa-box-open fa-2x mb-2"></i>
                            <p>아직 등록된 게시글이 없습니다.</p>
                        </div>'''
    html_content = re.sub(
        r'\{%\s*if\s+recent_posts\s*%\}.*?\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}',
        empty_posts_html,
        html_content,
        flags=re.DOTALL
    )
    
    # 8. {% for post in recent_posts %} ... {% endfor %} 처리
    html_content = re.sub(
        r'\{%\s*for\s+post\s+in\s+recent_posts\s*%\}.*?\{%\s*endfor\s*%\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # 9. {% for category in portfolio_categories %} ... {% endfor %} 처리
    html_content = re.sub(
        r'\{%\s*for\s+category\s+in\s+portfolio_categories\s*%\}.*?\{%\s*endfor\s*%\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # 10. 기타 변수들 처리
    html_content = re.sub(r'\{\{\s*post\.title\s*\}\}', '', html_content)
    html_content = re.sub(r'\{\{\s*post\.content\[:100\]\s*\}\}', '', html_content)
    html_content = re.sub(r'\{\{\s*post\.author_name\s*\}\}', '', html_content)
    html_content = re.sub(r'\{\{\s*post\.view_count\s*\}\}', '0', html_content)
    html_content = re.sub(r'\{\{\s*post\.created_at\.strftime\([^\)]+\)\s*if\s+post\.created_at\s+else\s+[\'"]\s*[\'"]\s*\}\}', '', html_content)
    html_content = re.sub(r'\{\{\s*post\.id\s*\}\}', '', html_content)
    html_content = re.sub(r'\{\{\s*post\.is_pinned\s*\}\}', 'false', html_content)
    html_content = re.sub(r'\{\{\s*post\.is_notice\s*\}\}', 'false', html_content)
    html_content = re.sub(r'\{\{\s*post\.file_path\s*\}\}', 'false', html_content)
    html_content = re.sub(r'\{\{\s*post\.content\|length\s*\}\}', '0', html_content)
    html_content = re.sub(r'\{\{\s*loop\.last\s*\}\}', 'false', html_content)
    html_content = re.sub(r'\{\{\s*category\.name\s*\}\}', '', html_content)
    
    # 11. JavaScript 내부의 Jinja2 문법 처리
    # const is_admin = {% if is_admin %}true{% else %}false{% endif %};
    html_content = re.sub(
        r'const\s+is_admin\s*=\s*\{%\s*if\s+is_admin\s*%\}true\{%\s*else\s*%\}false\{%\s*endif\s*%\};',
        'const is_admin = false;',
        html_content
    )
    
    # JavaScript 내부의 {% if not is_admin %} ... {% endif %} 처리 (개발자 도구 방지 코드 제거)
    # 이 부분은 통합 HTML에서는 필요 없으므로 제거
    html_content = re.sub(
        r'\{%\s*if\s+not\s+is_admin\s*%\}.*?\{%\s*endif\s*%\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # JavaScript 내부의 url_for() 처리 (이미지는 이미 처리됨)
    # 나머지 일반 경로만 처리
    html_content = re.sub(
        r'\{\{\s*url_for\([\'"]static[\'"],\s*filename=[\'"]([^\'"]+)[\'"]\)\s*\}\}',
        r"'/static/\1'",
        html_content
    )
    
    # 12. 남은 모든 Jinja2 문법 제거
    html_content = re.sub(r'\{%[^%]*%\}', '', html_content)
    html_content = re.sub(r'\{\{[^}]*\}\}', '', html_content)
    
    return html_content

def process_javascript(js_content, static_dir):
    """JavaScript 코드 개선 (통합 HTML용)"""
    if not js_content:
        return js_content
    
    print("   - JavaScript 코드 개선 중...")
    
    # JavaScript 내부의 이미지 경로를 base64로 변환
    # tryAlternativeImage 함수 내부의 이미지 경로 처리
    image_pattern_js_inline = r"'\{\{\s*url_for\([\'"]static[\'"],\s*filename=[\'"]images/([^\'"]+)[\'"]\)\s*\}\}(\?v=[^\'"]+)?'"
    
    def replace_js_image(match):
        filename = match.group(1)
        query_string = match.group(2) if match.group(2) else ''
        image_path = os.path.join(static_dir, 'images', filename)
        base64_data = encode_image_to_base64(image_path)
        if base64_data:
            print(f"      ✅ 이미지 인코딩 (JS 인라인): {filename}")
            return f"'{base64_data}'"
        else:
            print(f"      ⚠️  이미지 인코딩 실패: {filename}, 경로 사용")
            return f"'/static/images/{filename}{query_string}'"
    
    js_content = re.sub(image_pattern_js_inline, replace_js_image, js_content)
    
    # 포트폴리오 로딩 오류 처리 개선
    # loadPortfolio 함수 수정
    js_content = re.sub(
        r'async function loadPortfolio\([^)]*\)\s*\{[^}]*const response = await fetch\(`/portfolio\?category=\$\{category\}`\);',
        '''async function loadPortfolio(category = 'all', reset = false) {
    if (reset) {
        portfolioPage = 0;
        currentCategory = category;
    }
    
    const portfolioGrid = document.getElementById('portfolioGrid');
    if (!portfolioGrid) return;
    
    // 통합 HTML 파일에서는 API가 없으므로 바로 안내 메시지 표시
    if (window.location.protocol === 'file:' || !window.location.hostname || window.location.hostname === '') {
        portfolioGrid.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-images fa-3x text-muted mb-3"></i>
                <p class="text-muted">포트폴리오는 서버가 실행 중일 때만 표시됩니다.</p>
                <p class="text-muted small">통합 HTML 파일에서는 포트폴리오를 볼 수 없습니다.</p>
                <p class="text-muted small mt-2">서버를 실행하면 포트폴리오를 확인할 수 있습니다.</p>
            </div>
        `;
        return;
    }
    
    try {
        const response = await fetch(`/portfolio?category=${category}`);''',
        js_content,
        flags=re.DOTALL
    )
    
    # catch 블록 개선
    js_content = re.sub(
        r'catch\s*\(error\)\s*\{[^}]*포트폴리오를 불러오는 중 오류가 발생했습니다[^}]*\}',
        '''catch (error) {
                console.error('포트폴리오 로딩 오류:', error);
                portfolioGrid.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-images fa-3x text-muted mb-3"></i>
                        <p class="text-muted">포트폴리오는 서버가 실행 중일 때만 표시됩니다.</p>
                        <p class="text-muted small">통합 HTML 파일에서는 포트폴리오를 볼 수 없습니다.</p>
                    </div>
                `;
            }''',
        js_content,
        flags=re.DOTALL
    )
    
    return js_content

def create_integrated_html():
    """통합 HTML 파일 생성"""
    
    # 현재 스크립트 위치 기준으로 경로 설정
    script_path = os.path.abspath(__file__)
    base_dir = os.path.dirname(script_path)
    templates_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    print("=" * 60)
    print("통합 HTML 파일 생성 시작 (개선 버전)")
    print("=" * 60)
    print(f"기본 디렉토리: {base_dir}")
    print(f"템플릿 디렉토리: {templates_dir}")
    print(f"정적 파일 디렉토리: {static_dir}")
    
    # 파일 경로
    index_html_path = os.path.join(templates_dir, 'index.html')
    style_css_path = os.path.join(static_dir, 'css', 'style.css')
    main_js_path = os.path.join(static_dir, 'js', 'main.js')
    clean_preview_js_path = os.path.join(static_dir, 'js', 'clean_preview.js')
    output_path = os.path.join(base_dir, 'index_통합.html')
    
    # 1. index.html 읽기
    print("\n[1/5] index.html 읽는 중...")
    index_html = read_file(index_html_path)
    if not index_html:
        print("❌ index.html을 읽을 수 없습니다.")
        return False
    print(f"   ✅ {len(index_html)} 문자 읽음")
    
    # 2. style.css 읽기
    print("[2/5] style.css 읽는 중...")
    style_css = read_file(style_css_path)
    if not style_css:
        print("⚠️  style.css를 찾을 수 없습니다. CSS 없이 진행합니다.")
        style_css = ""
    else:
        print(f"   ✅ {len(style_css)} 문자 읽음")
    
    # 3. main.js 읽기
    print("[3/5] main.js 읽는 중...")
    main_js = read_file(main_js_path)
    if not main_js:
        print("⚠️  main.js를 찾을 수 없습니다. JS 없이 진행합니다.")
        main_js = ""
    else:
        print(f"   ✅ {len(main_js)} 문자 읽음")
    
    # 4. clean_preview.js 읽기
    print("[4/5] clean_preview.js 읽는 중...")
    clean_preview_js = read_file(clean_preview_js_path)
    if not clean_preview_js:
        print("⚠️  clean_preview.js를 찾을 수 없습니다. JS 없이 진행합니다.")
        clean_preview_js = ""
    else:
        print(f"   ✅ {len(clean_preview_js)} 문자 읽음")
    
    # 5. 통합 HTML 생성
    print("[5/5] 통합 HTML 생성 중...")
    
    # 5-1. 외부 CSS 링크 제거 (Flask 템플릿 문법 포함)
    print("   - 외부 CSS 링크 제거 중...")
    # url_for를 사용한 CSS 링크 제거
    index_html = re.sub(
        r'<link[^>]*href=["\']\{\{.*?url_for.*?style\.css.*?\}\}["\'][^>]*>',
        '',
        index_html
    )
    # 일반 CSS 링크는 유지 (Bootstrap, Font Awesome 등 CDN)
    
    # 5-2. Flask 템플릿 문법 처리 (static_dir 전달)
    index_html = process_flask_templates(index_html, static_dir)
    
    # 5-3. style.css를 <style> 태그에 추가
    print("   - CSS 파일 통합 중...")
    if style_css:
        style_pattern = r'(</style>)'
        index_html = re.sub(
            style_pattern,
            f'\n        /* ========== style.css 내용 ========== */\n        {style_css}\n    \\1',
            index_html,
            count=1
        )
    
    # 5-4. 외부 JavaScript 파일 참조 제거 및 인라인으로 변환
    print("   - JavaScript 파일 통합 중...")
    
    # 외부 main.js 파일 참조 제거
    index_html = re.sub(
        r'<script\s+src=["\']\{\{.*?main\.js.*?\}\}["\'][^>]*></script>',
        '',
        index_html
    )
    
    # 외부 clean_preview.js 파일 참조 제거 (있다면)
    index_html = re.sub(
        r'<script\s+src=["\']\{\{.*?clean_preview\.js.*?\}\}["\'][^>]*></script>',
        '',
        index_html
    )
    
    # main.js 처리 (static_dir 전달)
    main_js = process_javascript(main_js, static_dir)
    
    js_content = ""
    if main_js:
        js_content += f'\n    <!-- ========== main.js 내용 ========== -->\n    <script>\n{main_js}\n    </script>'
    if clean_preview_js:
        js_content += f'\n    <!-- ========== clean_preview.js 내용 ========== -->\n    <script>\n{clean_preview_js}\n    </script>'
    
    # </body> 태그 전에 JavaScript 추가 (기존 인라인 스크립트는 유지)
    if js_content:
        body_end_pattern = r'(</body>)'
        index_html = re.sub(
            body_end_pattern,
            f'{js_content}\\1',
            index_html,
            count=1
        )
    
    # 5-5. 최종 검증: 남은 Jinja2 문법 확인
    remaining_jinja = re.findall(r'\{%[^%]*%\}|\{\{[^}]*\}\}', index_html)
    if remaining_jinja:
        print(f"⚠️  경고: {len(remaining_jinja)}개의 Jinja2 문법이 남아있습니다.")
        for i, jinja in enumerate(remaining_jinja[:5]):  # 처음 5개만 표시
            print(f"      {i+1}. {jinja[:50]}")
    
    # 파일 저장
    print("\n   - 파일 저장 중...")
    if write_file(output_path, index_html):
        print("\n" + "=" * 60)
        print("✅ 통합 HTML 파일 생성 완료!")
        print(f"📁 파일 위치: {output_path}")
        print(f"📊 파일 크기: {len(index_html):,} 문자")
        print("=" * 60)
        return True
    else:
        print("\n❌ 파일 저장 실패")
        return False

if __name__ == "__main__":
    create_integrated_html()

