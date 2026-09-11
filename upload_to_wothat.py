# -*- coding: utf-8 -*-
import os
import sys
import requests
import json

# Ensure utf-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "https://images.wothat.com"
UPLOAD_URL = f"{BASE_URL}/upload"
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")

IMAGES = [
    "fishbone_diagram.png",
    "pareto_chart.png",
    "control_chart.png",
    "evm_chart.png",
    "network_cpm_chart.png",
    "stakeholder_matrix.png",
    "budget_hierarchy.png"
]

def try_login_session(password):
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    # Try user login
    try:
        r = session.post(f"{BASE_URL}/api/auth/login", json={'authCode': password}, timeout=10)
        print("Login with authCode status:", r.status_code, r.text)
        if r.status_code == 200:
            return session
    except Exception as e:
        print("Login with authCode error:", e)

    # Try admin login with username admin or adminPassword
    for u in ['admin', 'root', '']:
        try:
            payload = {'username': u, 'password': password} if u else {'password': password}
            r = session.post(f"{BASE_URL}/api/auth/login", json=payload, timeout=10)
            print(f"Login as {u} status:", r.status_code, r.text)
            if r.status_code == 200:
                return session
        except Exception as e:
            pass

    return session

def upload_single_image(session, image_name, auth_code=None):
    img_path = os.path.join(IMAGES_DIR, image_name)
    if not os.path.exists(img_path):
        print(f"[ERROR] Image not found: {img_path}")
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'authCode': auth_code if auth_code else ''
    }
    params = {'authCode': auth_code} if auth_code else {}

    with open(img_path, 'rb') as f:
        files = {
            'file': (image_name, f, 'image/png')
        }
        try:
            print(f"Uploading {image_name} ...")
            resp = session.post(UPLOAD_URL, files=files, params=params, headers=headers, timeout=25)
            print(f"Response [{resp.status_code}]: {resp.text}")
            if resp.status_code == 200:
                data = resp.json()
                url = None
                if isinstance(data, list) and len(data) > 0:
                    url = data[0].get('src') or data[0].get('url')
                elif isinstance(data, dict):
                    url = data.get('url') or data.get('src')
                    if not url and 'data' in data and isinstance(data['data'], dict):
                        url = data['data'].get('url') or data['data'].get('src')
                
                if url:
                    if url.startswith('/'):
                        url = f"{BASE_URL}{url}"
                    print(f"[SUCCESS] {image_name} -> {url}")
                    return url
                else:
                    print(f"[WARN] No URL in response: {resp.text}")
                    return None
            else:
                print(f"[FAILED] [{resp.status_code}]: {resp.text}")
                return None
        except Exception as e:
            print(f"[EXCEPTION]: {e}")
            return None

def update_markdown_files(url_mapping):
    md_files = [
        os.path.join(os.path.dirname(__file__), "系统集成项目管理工程师（第3版）核心知识点速记手册.md"),
        os.path.join(os.path.dirname(__file__), "README.md")
    ]
    for file_path in md_files:
        if not os.path.exists(file_path):
            continue
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        changed = False
        for img_name, online_url in url_mapping.items():
            if online_url:
                local_pattern = f"./images/{img_name}"
                if local_pattern in content:
                    content = content.replace(local_pattern, online_url)
                    changed = True
        
        if changed:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[UPDATED] {os.path.basename(file_path)}")

def main():
    auth_code = sys.argv[1].strip() if len(sys.argv) > 1 else 'fingal123'
    session = try_login_session(auth_code)

    url_mapping = {}
    success_count = 0
    for img in IMAGES:
        url = upload_single_image(session, img, auth_code)
        if url:
            url_mapping[img] = url
            success_count += 1

    print(f"\nStats: Success {success_count} / {len(IMAGES)}")
    if success_count > 0:
        update_markdown_files(url_mapping)
        print("\nAll uploaded image URLs have been updated in Markdown files!")

if __name__ == "__main__":
    main()
