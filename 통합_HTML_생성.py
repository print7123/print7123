#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
홈페이지를 하나의 통합 HTML 파일로 생성하는 스크립트
외부 CSS, JS 파일을 모두 인라인으로 포함합니다.
"""

import os
import re

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
    except Exception as e:
        print(f"❌ 파일 쓰기 오류 ({filepath}): {e}")

def create_integrated_html():
    """통합 HTML 파일 생성"""
    
    # 현재 스크립트 위치 기준으로 경로 설정
    script_path = os.path.abspath(__file__)
    base_dir = os.path.dirname(script_path)
    templates_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    print(f"기본 디렉토리: {base_dir}")
    print(f"템플릿 디렉토리: {templates_dir}")
    print(f"정적 파일 디렉토리: {static_dir}")
    
    # 파일 경로
    index_html_path = os.path.join(templates_dir, 'index.html')
    style_css_path = os.path.join(static_dir, 'css', 'style.css')
    main_js_path = os.path.join(static_dir, 'js', 'main.js')
    clean_preview_js_path = os.path.join(static_dir, 'js', 'clean_preview.js')
    output_path = os.path.join(base_dir, 'index_통합.html')
    
    print("=" * 60)
    print("통합 HTML 파일 생성 시작")
    print("=" * 60)
    
    # 1. index.html 읽기
    print("\n[1/5] index.html 읽는 중...")
    index_html = read_file(index_html_path)
    if not index_html:
        return False
    
    # 2. style.css 읽기
    print("[2/5] style.css 읽는 중...")
    style_css = read_file(style_css_path)
    if not style_css:
        print("⚠️  style.css를 찾을 수 없습니다. CSS 없이 진행합니다.")
        style_css = ""
    
    # 3. main.js 읽기
    print("[3/5] main.js 읽는 중...")
    main_js = read_file(main_js_path)
    if not main_js:
        print("⚠️  main.js를 찾을 수 없습니다. JS 없이 진행합니다.")
        main_js = ""
    
    # 4. clean_preview.js 읽기
    print("[4/5] clean_preview.js 읽는 중...")
    clean_preview_js = read_file(clean_preview_js_path)
    if not clean_preview_js:
        print("⚠️  clean_preview.js를 찾을 수 없습니다. JS 없이 진행합니다.")
        clean_preview_js = ""
    
    # 5. 통합 HTML 생성
    print("[5/5] 통합 HTML 생성 중...")
    
    # 외부 CSS 링크 제거 및 인라인 CSS 추가
    # <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet"> 제거
    index_html = re.sub(
        r'<link\s+href=["\']{{ url_for\([\'"]static[\'"],\s*filename=[\'"]css/style\.css[\'"]\)\s*}}["\']\s+rel=["\']stylesheet["\']\s*>',
        '',
        index_html
    )
    
    # Flask 템플릿 문법을 기본값으로 대체
    print("   - Flask 템플릿 문법 처리 중...")
    
    # url_for() 함수를 실제 경로로 대체
    index_html = re.sub(
        r'{{ url_for\([\'"]static[\'"],\s*filename=[\'"]([^\'"]+)[\'"]\)\s*}}',
        r'/static/\1',
        index_html
    )
    
    # 이미지 경로 수정 (main_header.png.jpg)
    index_html = re.sub(
        r'/static/images/main_header\.png\.jpg',
        '/static/images/main_header.png.jpg',
        index_html
    )
    
    # portfolio_categories 루프 처리 (기본 카테고리로 대체)
    portfolio_categories_html = """
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('전단지')">전단지</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('명함')">명함</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('책자')">책자</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('포스터')">포스터</button>
                    <button type="button" class="btn btn-outline-primary" onclick="filterPortfolio('브로슈어')">브로슈어</button>
"""
    index_html = re.sub(
        r'{%\s*if\s+portfolio_categories\s*%}.*?{%\s*endif\s*%}',
        portfolio_categories_html,
        index_html,
        flags=re.DOTALL
    )
    
    # recent_posts 루프 처리 (빈 상태로 대체)
    index_html = re.sub(
        r'{%\s*if\s+recent_posts\s*%}.*?{%\s*else\s*%}.*?{%\s*endif\s*%}',
        '<div class="p-3 text-center text-muted"><i class="fas fa-box-open fa-2x mb-2"></i><p>아직 등록된 게시글이 없습니다.</p></div>',
        index_html,
        flags=re.DOTALL
    )
    
    # 기타 Flask 변수들 기본값으로 대체
    index_html = re.sub(r'{{\s*is_admin\s*}}', 'false', index_html)
    index_html = re.sub(r'{{\s*is_authenticated\s*}}', 'false', index_html)
    
    # {% if not is_admin %} ... {% else %} ... {% endif %} 처리
    # 견적 계산기 보호 메시지 (관리자가 아닌 경우)
    index_html = re.sub(
        r'{%\s*if\s+not\s+is_admin\s*%}.*?{%\s*else\s*%}.*?{%\s*endif\s*%}',
        '''<div class="alert alert-info mb-3">
                                <i class="fas fa-lock me-2"></i>
                                <strong>견적 계산기 보호:</strong> 이 영역은 보호되어 있습니다. 견적 계산만 가능하며 수정/삭제는 관리자만 가능합니다.
                            </div>''',
        index_html,
        flags=re.DOTALL
    )
    
    # {% if is_admin %} ... {% endif %} 처리 (관리자 대시보드 버튼 등)
    index_html = re.sub(r'{%\s*if\s+is_admin\s*%}.*?{%\s*endif\s*%}', '', index_html, flags=re.DOTALL)
    
    # {% if is_authenticated %} ... {% else %} ... {% endif %} 처리
    index_html = re.sub(
        r'{%\s*if\s+is_authenticated\s*%}.*?{%\s*else\s*%}.*?{%\s*endif\s*%}', 
        '<a href="/login" class="btn btn-outline-primary btn-lg px-3"><i class="fas fa-sign-in-alt me-2"></i>로그인</a>',
        index_html, 
        flags=re.DOTALL
    )
    
    # <style> 태그 찾기 (인쇄용 CSS 이후)
    # 기존 <style> 태그 안에 style.css 내용 추가
    style_pattern = r'(</style>)'
    if style_css:
        # 기존 스타일 태그 닫기 전에 style.css 내용 추가
        index_html = re.sub(
            style_pattern,
            f'\n        /* ========== style.css 내용 ========== */\n        {style_css}\n    \\1',
            index_html,
            count=1
        )
    else:
        # style.css가 없으면 기존 스타일만 유지
        pass
    
    # 외부 JS 파일 참조 제거 (이미 인라인으로 포함되어 있을 수 있음)
    # <script src="..."> 태그는 그대로 유지 (Flask 템플릿에서 동적으로 생성될 수 있음)
    
    # </body> 태그 전에 JS 파일들 추가
    # 먼저 기존 인라인 스크립트가 있는지 확인
    body_end_pattern = r'(</body>)'
    
    # main.js와 clean_preview.js를 </body> 전에 추가
    # 포트폴리오 로딩 오류 처리 개선
    if main_js:
        # loadPortfolio 함수의 오류 처리를 개선
        # catch 블록의 오류 메시지를 더 친화적으로 변경
        main_js = re.sub(
            r'catch\s*\(error\)\s*\{[^}]*portfolioGrid\.innerHTML\s*=.*?오류가 발생했습니다[^}]*\}',
            '''catch (error) {
                console.error('포트폴리오 로딩 오류:', error);
                portfolioGrid.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-images fa-3x text-muted mb-3"></i>
                        <p class="text-muted">포트폴리오는 서버가 실행 중일 때만 표시됩니다.</p>
                        <p class="text-muted small">통합 HTML 파일에서는 포트폴리오를 볼 수 없습니다.</p>
                        <p class="text-muted small mt-2">서버를 실행하면 포트폴리오를 확인할 수 있습니다.</p>
                    </div>
                `;
            }''',
            main_js,
            flags=re.DOTALL
        )
        
        # fetch 호출 전에 서버 연결 확인
        main_js = re.sub(
            r'const response = await fetch\(`/portfolio\?category=\$\{category\}`\);',
            '''// 통합 HTML 파일에서는 API가 없으므로 바로 오류 처리
        if (window.location.protocol === 'file:') {
            portfolioGrid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-images fa-3x text-muted mb-3"></i>
                    <p class="text-muted">포트폴리오는 서버가 실행 중일 때만 표시됩니다.</p>
                    <p class="text-muted small">통합 HTML 파일에서는 포트폴리오를 볼 수 없습니다.</p>
                </div>
            `;
            return;
        }
        const response = await fetch(`/portfolio?category=${category}`);''',
            main_js
        )
    
    js_content = ""
    if main_js:
        js_content += f'\n    <!-- ========== main.js 내용 ========== -->\n    <script>\n{main_js}\n    </script>'
    if clean_preview_js:
        js_content += f'\n    <!-- ========== clean_preview.js 내용 ========== -->\n    <script>\n{clean_preview_js}\n    </script>'
    
    if js_content:
        index_html = re.sub(
            body_end_pattern,
            f'{js_content}\\1',
            index_html,
            count=1
        )
    
    # 파일 저장
    write_file(output_path, index_html)
    
    print("\n" + "=" * 60)
    print("✅ 통합 HTML 파일 생성 완료!")
    print(f"📁 파일 위치: {output_path}")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    create_integrated_html()

