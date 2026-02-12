#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
14시경 작동했던 홈페이지 파일 복원 스크립트
백업 폴더의 파일을 홈페이지_최종분_26.02.11로 복원
"""

import os
import shutil
from datetime import datetime

def restore_working_files():
    """14시경 작동했던 파일 복원"""
    
    # 현재 스크립트 위치
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # 백업 폴더 경로
    backup_folder = os.path.join(base_dir, "현재작동파일_백업_1", "현재작동파일_백업_20250913_204500")
    target_folder = script_dir  # 홈페이지_최종분_26.02.11
    
    print("=" * 60)
    print("최종 복원 - 14시 작동 파일")
    print("=" * 60)
    print()
    
    # 백업 폴더 확인
    if not os.path.exists(backup_folder):
        print(f"❌ 백업 폴더를 찾을 수 없습니다: {backup_folder}")
        return False
    
    print(f"[1/5] 백업 폴더 확인: {backup_folder}")
    print(f"      ✅ 백업 폴더 발견")
    print()
    
    # 기존 파일 백업
    print("[2/5] 기존 파일 백업 중...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dest = os.path.join(target_folder, f"백업_복원전_{timestamp}")
    
    if not os.path.exists(backup_dest):
        os.makedirs(backup_dest, exist_ok=True)
        
        # 주요 파일 백업
        files_to_backup = [
            "app_enhanced_작동중.py",
            "email_config.py",
            "requirements.txt"
        ]
        
        for file in files_to_backup:
            src = os.path.join(target_folder, file)
            if os.path.exists(src):
                shutil.copy2(src, backup_dest)
        
        # 폴더 백업
        folders_to_backup = ["templates", "static"]
        for folder in folders_to_backup:
            src = os.path.join(target_folder, folder)
            if os.path.exists(src):
                dest = os.path.join(backup_dest, folder)
                shutil.copytree(src, dest, dirs_exist_ok=True)
        
        print(f"      ✅ 백업 완료: {backup_dest}")
    else:
        print(f"      ⚠️  백업 폴더가 이미 존재합니다.")
    print()
    
    # 파일 복원
    print("[3/5] 파일 복원 중...")
    
    # 1. app_enhanced_작동중.py 복원
    src_file = os.path.join(backup_folder, "app_enhanced_작동중.py")
    dest_file = os.path.join(target_folder, "app_enhanced_작동중.py")
    if os.path.exists(src_file):
        shutil.copy2(src_file, dest_file)
        print(f"      ✅ app_enhanced_작동중.py 복원 완료")
    else:
        print(f"      ❌ app_enhanced_작동중.py 없음")
    
    # 2. templates 폴더 복원
    src_templates = os.path.join(backup_folder, "templates")
    dest_templates = os.path.join(target_folder, "templates")
    if os.path.exists(src_templates):
        if os.path.exists(dest_templates):
            shutil.rmtree(dest_templates)
        shutil.copytree(src_templates, dest_templates)
        print(f"      ✅ templates 폴더 복원 완료")
    else:
        print(f"      ⚠️  templates 폴더 없음")
    
    # 3. static 폴더 복원
    src_static = os.path.join(backup_folder, "static")
    dest_static = os.path.join(target_folder, "static")
    if os.path.exists(src_static):
        if os.path.exists(dest_static):
            shutil.rmtree(dest_static)
        shutil.copytree(src_static, dest_static)
        print(f"      ✅ static 폴더 복원 완료")
    else:
        print(f"      ⚠️  static 폴더 없음")
    
    # 4. requirements.txt 복원
    src_req = os.path.join(backup_folder, "requirements.txt")
    dest_req = os.path.join(target_folder, "requirements.txt")
    if os.path.exists(src_req):
        shutil.copy2(src_req, dest_req)
        print(f"      ✅ requirements.txt 복원 완료")
    
    # 5. email_config.py 복원
    src_email = os.path.join(backup_folder, "email_config.py")
    dest_email = os.path.join(target_folder, "email_config.py")
    if os.path.exists(src_email):
        shutil.copy2(src_email, dest_email)
        print(f"      ✅ email_config.py 복원 완료")
    
    # 6. instance 폴더 복원 (데이터베이스)
    src_instance = os.path.join(backup_folder, "instance")
    dest_instance = os.path.join(target_folder, "instance")
    if os.path.exists(src_instance):
        if not os.path.exists(dest_instance):
            os.makedirs(dest_instance, exist_ok=True)
        for item in os.listdir(src_instance):
            src_item = os.path.join(src_instance, item)
            dest_item = os.path.join(dest_instance, item)
            if os.path.isdir(src_item):
                if os.path.exists(dest_item):
                    shutil.rmtree(dest_item)
                shutil.copytree(src_item, dest_item)
            else:
                shutil.copy2(src_item, dest_item)
        print(f"      ✅ instance 폴더 복원 완료")
    
    print()
    
    # 복원 확인
    print("[4/5] 복원 확인 중...")
    check_files = [
        ("app_enhanced_작동중.py", os.path.join(target_folder, "app_enhanced_작동중.py")),
        ("templates/index.html", os.path.join(target_folder, "templates", "index.html")),
        ("static/js/main.js", os.path.join(target_folder, "static", "js", "main.js")),
        ("static/css/style.css", os.path.join(target_folder, "static", "css", "style.css")),
    ]
    
    all_ok = True
    for name, path in check_files:
        if os.path.exists(path):
            print(f"      ✅ {name} 확인")
        else:
            print(f"      ❌ {name} 없음")
            all_ok = False
    
    print()
    
    # 완료 메시지
    print("[5/5] 복원 완료!")
    print()
    print("=" * 60)
    print("✅ 복원 완료!")
    print("=" * 60)
    print()
    print("복원된 파일:")
    print("  - app_enhanced_작동중.py")
    print("  - templates/ 폴더 (모든 HTML 파일)")
    print("  - static/ 폴더 (CSS, JS, 이미지)")
    print("  - requirements.txt")
    print("  - email_config.py")
    print("  - instance/ 폴더 (데이터베이스)")
    print()
    print("서버를 시작하려면:")
    print("  → 🚀_서버_시작_최종분.bat 파일을 실행하세요")
    print()
    print("=" * 60)
    
    return all_ok

if __name__ == "__main__":
    try:
        restore_working_files()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n아무 키나 누르면 종료됩니다...")



