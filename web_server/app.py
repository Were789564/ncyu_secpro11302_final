from flask import Flask, request, render_template, redirect, url_for, session, make_response
import secrets
import requests
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'web_database.db')

# 初始化資料庫
def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 建立 users 資料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 建立 comments 資料表 (用於 Stored XSS)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 插入測試用戶資料
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)",
                   ('admin', 'adminpass', 'admin@example.com'))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)",
                   ('user', 'userpass', 'user@example.com'))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)",
                   ('test', 'testpass', 'test@example.com'))

    conn.commit()
    conn.close()
    print("資料庫初始化完成！")

# 資料庫連接函數
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 從資料庫驗證用戶帳號密碼
def authenticate_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                       (username, password)).fetchone()
    conn.close()
    return user

# 從資料庫獲取用戶資料
def get_user(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

# 更新用戶資料到資料庫
def update_user(username, email=None, password=None):
    conn = get_db_connection()
    if email:
        conn.execute('UPDATE users SET email = ? WHERE username = ?', (email, username))
    if password:
        conn.execute('UPDATE users SET password = ? WHERE username = ?', (password, username))
    conn.commit()
    conn.close()

# 獲取所有留言
def get_comments():
    conn = get_db_connection()
    comments = conn.execute('SELECT * FROM comments ORDER BY created_at DESC').fetchall()
    conn.close()
    return comments

# 新增留言
def add_comment(username, message):
    conn = get_db_connection()
    conn.execute('INSERT INTO comments (username, message) VALUES (?, ?)', (username, message))
    conn.commit()
    conn.close()

# 產生 CSRF token
def generate_csrf_token():
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # 使用資料庫驗證帳號密碼
        user = authenticate_user(username, password)
        if user:
            session['username'] = username
            generate_csrf_token()
            return redirect(url_for('comment'))
        return render_template('login.html', error='登入失敗，請檢查帳號密碼')
    return render_template('login.html')

@app.route('/comment', methods=['GET', 'POST'])
def comment():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        msg = request.form['message']
        # 將留言存儲到資料庫中 (Stored XSS 漏洞點)
        add_comment(session['username'], msg)
    
    # 從資料庫獲取所有留言
    comments = get_comments()
    csrf_token = generate_csrf_token()  # 每次都生成新的 CSRF token
    return render_template('comment.html', comments=comments, csrf_token=csrf_token, username=session['username'])

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 嚴格的 CSRF 保護
        submitted_token = request.form.get('csrf_token')
        session_token = session.get('csrf_token')
        
        if not submitted_token or not session_token or submitted_token != session_token:
            return render_template('account.html', 
                                 csrf_token=session.get('csrf_token'),
                                 user=get_user(session['username']),
                                 error='CSRF token 驗證失敗！請重新提交。')
        
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        
        if email or new_password:
            update_user(session['username'], email, new_password)
            # 密碼修改後生成新的 CSRF token
            generate_csrf_token()
            
            user = get_user(session['username'])
            return render_template('account.html', 
                                 csrf_token=session.get('csrf_token'),
                                 user=user, 
                                 success='資料更新成功！如修改密碼請重新登入。')
    
    # GET 請求時生成新的 CSRF token
    csrf_token = generate_csrf_token()
    user = get_user(session['username'])
    return render_template('account.html', 
                         csrf_token=csrf_token,
                         user=user)

@app.route("/fetch")
def fetch():
    """SSRF 漏洞端點 - 僅限管理員使用"""
    # 檢查用戶是否已登入且為 admin
    if 'username' not in session:
        return '''
        <h1>🔒 需要登入</h1>
        <p>此功能需要管理員權限</p>
        <p><a href="/login">請先登入</a></p>
        ''', 401
    
    if session['username'] != 'admin':
        return '''
        <h1>🚫 權限不足</h1>
        <p>此功能僅限管理員使用</p>
        <p>當前用戶: <strong>{}</strong></p>
        <p><a href="/comment">返回留言板</a></p>
        '''.format(session['username']), 403
    
    # 檢查是否只有 path 參數
    allowed_params = {'path'}
    received_params = set(request.args.keys())
    
    if received_params - allowed_params:
        invalid_params = received_params - allowed_params
        return f"""
        <h1>❌ 參數錯誤</h1>
        <p>此端點只接受 'path' 參數</p>
        <p>不被允許的參數: <strong>{', '.join(invalid_params)}</strong></p>
        <p><a href="/fetch">返回 Fetch 工具</a></p>
        """, 400
    
    path = request.args.get("path")
    
    if not path:
        return """
        <h1>🌐 管理員專用 URL Fetch Service</h1>
        <p>此服務可以幫管理員獲取任何 URL 的內容</p>
        <p><strong>用法:</strong> /fetch?path=http://example.com</p>
        <hr>
        <h3>📋 內部服務範例:</h3>
        <ul>
            <li><a href="/fetch?path=http://127.0.0.1:8080/">內部服務狀態</a></li>
            <li><a href="/fetch?path=http://127.0.0.1:8080/employees">員工資料</a></li>
            <li><a href="/fetch?path=http://127.0.0.1:8080/financial">財務資料</a></li>
            <li><a href="/fetch?path=http://127.0.0.1:8080/logs">系統日誌</a></li>
            <li><a href="/fetch?path=http://127.0.0.1:8080/sql_debug?query=SELECT * FROM employees">SQL 調試</a></li>
        </ul>
        <h3>🌍 外部測試範例:</h3>
        <ul>
            <li><a href="/fetch?path=http://httpbin.org/ip">查看外部 IP</a></li>
            <li><a href="/fetch?path=http://httpbin.org/headers">查看請求標頭</a></li>
        </ul>
        <p style="color: red;">⚠️ 警告：此功能可能被用於 SSRF 攻擊，請謹慎使用</p>
        <p><a href="/comment">返回留言板</a></p>
        """
    
    try:
        print(f"[SSRF] Admin {session['username']} fetching: {path}")
        response = requests.get(path, timeout=10)
        
        # 如果是 JSON 回應，美化顯示
        try:
            import json
            json_data = response.json()
            formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
            return f"""
            <h1>📊 管理員 Fetch 結果</h1>
            <p><strong>URL:</strong> {path}</p>
            <p><strong>狀態碼:</strong> {response.status_code}</p>
            <p><strong>操作者:</strong> {session['username']}</p>
            <hr>
            <pre style="background: #f8f9fa; padding: 1rem; border-radius: 5px; overflow-x: auto;">{formatted_json}</pre>
            <p><a href="/fetch">返回 Fetch 工具</a> | <a href="/comment">返回留言板</a></p>
            """
        except:
            # 如果不是 JSON，直接返回
            return f"""
            <h1>📄 管理員 Fetch 結果</h1>
            <p><strong>URL:</strong> {path}</p>
            <p><strong>狀態碼:</strong> {response.status_code}</p>
            <p><strong>操作者:</strong> {session['username']}</p>
            <hr>
            <pre style="background: #f8f9fa; padding: 1rem; border-radius: 5px; overflow-x: auto; white-space: pre-wrap;">{response.text}</pre>
            <p><a href="/fetch">返回 Fetch 工具</a> | <a href="/comment">返回留言板</a></p>
            """
            
    except requests.exceptions.ConnectionError:
        return f"""
        <h1>❌ 連接錯誤</h1>
        <p>無法連接到: <strong>{path}</strong></p>
        <p>可能原因：目標服務未運行或網路問題</p>
        <p><a href="/fetch">返回 Fetch 工具</a></p>
        """, 500
    except requests.exceptions.Timeout:
        return f"""
        <h1>⏰ 請求超時</h1>
        <p>請求超時: <strong>{path}</strong></p>
        <p><a href="/fetch">返回 Fetch 工具</a></p>
        """, 500
    except Exception as e:
        return f"""
        <h1>💥 發生錯誤</h1>
        <p>錯誤信息: <strong>{str(e)}</strong></p>
        <p>URL: <strong>{path}</strong></p>
        <p><a href="/fetch">返回 Fetch 工具</a></p>
        """, 500
            
    except requests.exceptions.ConnectionError:
        return f"""
        <h1>❌ 連接錯誤</h1>
        <p>無法連接到: <strong>{path}</strong></p>
        <p>可能原因：目標服務未運行或網路問題</p>
        <p><a href="/fetch">返回 Fetch 工具</a></p>
        """, 500
    except requests.exceptions.Timeout:
        return f"""
        <h1>⏰ 請求超時</h1>
        <p>請求超時: <strong>{path}</strong></p>
        <p><a href="/fetch">返回 Fetch 工具</a></p>
        """, 500
    except Exception as e:
        return f"""
        <h1>💥 發生錯誤</h1>
        <p>錯誤信息: <strong>{str(e)}</strong></p>
        <p>URL: <strong>{path}</strong></p>
        <p><a href="/fetch">返回 Fetch 工具</a></p>
        """, 500

# 新增管理員功能查看資料庫內容
@app.route('/admin/comments')
def admin_comments():
    if 'username' not in session or session['username'] != 'admin':
        return 'Access Denied', 403
    
    conn = get_db_connection()
    comments = conn.execute('SELECT * FROM comments ORDER BY created_at DESC').fetchall()
    conn.close()
    
    html = '''
    <h1>📝 資料庫中的所有留言</h1>
    <style>table {border-collapse: collapse; width: 100%;} th, td {border: 1px solid #ddd; padding: 8px; text-align: left;} th {background-color: #f2f2f2;}</style>
    <table>
        <tr><th>ID</th><th>用戶</th><th>留言內容</th><th>時間</th></tr>
    '''
    for comment in comments:
        # 高亮顯示可能的惡意腳本
        message = comment["message"]
        if '<script>' in message or '<img' in message or '<svg' in message:
            message = f'<span style="background: #ffebee; color: #c62828; font-weight: bold;">⚠️ {message}</span>'
        
        html += f'<tr><td>{comment["id"]}</td><td>{comment["username"]}</td><td>{message}</td><td>{comment["created_at"]}</td></tr>'
    
    html += '</table><br><a href="/admin/users">查看用戶</a> | <a href="/comment">返回留言板</a>'
    return html

@app.route('/admin/users')
def admin_users():
    if 'username' not in session or session['username'] != 'admin':
        return 'Access Denied', 403
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    
    html = '''
    <h1>👥 資料庫中的所有用戶</h1>
    <style>table {border-collapse: collapse; width: 100%;} th, td {border: 1px solid #ddd; padding: 8px; text-align: left;} th {background-color: #f2f2f2;}</style>
    <table>
        <tr><th>ID</th><th>用戶名</th><th>密碼</th><th>郵箱</th><th>創建時間</th></tr>
    '''
    for user in users:
        # 高亮顯示被修改的帳號
        username_display = user["username"]
        password_display = user["password"]
        email_display = user["email"] or "未設定"
        
        if user["password"] == "hacked123":
            password_display = f'<span style="background: #ffebee; color: #c62828; font-weight: bold;">🚨 {password_display}</span>'
        
        if user["email"] and ("hacker" in user["email"] or "evil" in user["email"]):
            email_display = f'<span style="background: #ffebee; color: #c62828; font-weight: bold;">🚨 {email_display}</span>'
        
        html += f'<tr><td>{user["id"]}</td><td>{username_display}</td><td>{password_display}</td><td>{email_display}</td><td>{user["created_at"]}</td></tr>'
    
    html += '</table><br><a href="/admin/comments">查看留言</a> | <a href="/comment">返回留言板</a>'
    return html

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    # 導入 datetime 用於時間戳
    from datetime import datetime
    # 啟動前自動初始化資料庫
    init_database()
    print("伺服器啟動中...")
    print("請在瀏覽器中訪問: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
