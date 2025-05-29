from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'internal_database.db')

# 初始化內部資料庫
def init_internal_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 員工資料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        position TEXT NOT NULL,
        salary INTEGER NOT NULL,
        department TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        hire_date DATE,
        security_clearance TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 系統日誌表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        level TEXT NOT NULL,
        service TEXT NOT NULL,
        message TEXT NOT NULL,
        ip_address TEXT
    )
    ''')
    
    # 財務資料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS financial_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT UNIQUE NOT NULL,
        amount DECIMAL(15,2) NOT NULL,
        transaction_type TEXT NOT NULL,
        account_number TEXT NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 插入敏感員工資料
    employees_data = [
        ('EMP001', '張三', 'CEO', 2500000, 'Executive', '0912-345-678', 'ceo@company.com', '2020-01-01', 'TOP_SECRET'),
        ('EMP002', '李四', 'CTO', 1800000, 'Technology', '0923-456-789', 'cto@company.com', '2020-02-15', 'SECRET'),
        ('EMP003', '王五', '資安主管', 1200000, 'Security', '0934-567-890', 'security@company.com', '2021-03-10', 'SECRET'),
        ('EMP004', '趙六', '財務經理', 900000, 'Finance', '0945-678-901', 'finance@company.com', '2021-06-01', 'CONFIDENTIAL'),
        ('EMP005', '孫七', '系統管理員', 800000, 'IT', '0956-789-012', 'admin@company.com', '2022-01-15', 'CONFIDENTIAL'),
        ('EMP006', '周八', '軟體工程師', 700000, 'Development', '0967-890-123', 'dev@company.com', '2022-08-01', 'RESTRICTED')
    ]
    
    for emp in employees_data:
        cursor.execute("""INSERT OR IGNORE INTO employees 
                         (employee_id, name, position, salary, department, phone, email, hire_date, security_clearance) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", emp)
    
    # 插入系統日誌
    logs_data = [
        ('INFO', 'AUTH', '用戶 admin 登入成功', '192.168.1.100'),
        ('WARNING', 'SECURITY', '檢測到可疑的 SQL 查詢嘗試', '192.168.1.105'),
        ('ERROR', 'DATABASE', '資料庫連接失敗', '127.0.0.1'),
        ('INFO', 'BACKUP', '每日備份完成', '127.0.0.1'),
        ('CRITICAL', 'SECURITY', '管理員密碼被修改', '192.168.1.100'),
        ('WARNING', 'ACCESS', '未授權訪問 /admin 端點', '192.168.1.108')
    ]
    
    for log in logs_data:
        cursor.execute("INSERT OR IGNORE INTO system_logs (level, service, message, ip_address) VALUES (?, ?, ?, ?)", log)
    
    # 插入財務資料
    financial_data = [
        ('TXN001', 50000000.00, 'INCOME', 'ACC-001', '客戶付款 - 專案A'),
        ('TXN002', -2500000.00, 'EXPENSE', 'ACC-002', 'CEO 薪資'),
        ('TXN003', 30000000.00, 'INCOME', 'ACC-003', '政府合約款項'),
        ('TXN004', -15000000.00, 'EXPENSE', 'ACC-004', '設備採購'),
        ('TXN005', 80000000.00, 'INCOME', 'ACC-005', '年度主要合約'),
        ('TXN006', -500000.00, 'EXPENSE', 'ACC-006', '資安設備更新')
    ]
    
    for fin in financial_data:
        cursor.execute("INSERT OR IGNORE INTO financial_data (transaction_id, amount, transaction_type, account_number, description) VALUES (?, ?, ?, ?, ?)", fin)
    
    conn.commit()
    conn.close()
    print("內部資料庫初始化完成！")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 檢查來源 IP 是否為允許的 Web 伺服器
def is_allowed_source():
    client_ip = request.remote_addr
    # 只允許 web_server (127.0.0.1) 訪問
    allowed_ips = ['127.0.0.1', '::1', 'localhost']
    
    # 在實際環境中，這裡會是 web_server 的具體 IP
    return client_ip in allowed_ips

@app.before_request
def check_access():
    if not is_allowed_source():
        return jsonify({
            'error': 'Access Denied', 
            'message': 'This internal service can only be accessed from authorized servers',
            'your_ip': request.remote_addr,
            'allowed_ips': ['127.0.0.1']
        }), 403

@app.route('/')
def index():
    return jsonify({
        'service': 'Internal Management System',
        'version': '2.1.0',
        'status': 'running',
        'endpoints': [
            '/employees',
            '/logs', 
            '/financial',
            '/sql_debug',
            '/health'
        ],
        'warning': 'INTERNAL USE ONLY - Contains sensitive company data'
    })

@app.route('/employees')
def get_employees():
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees ORDER BY salary DESC').fetchall()
    conn.close()
    
    return jsonify({
        'total_employees': len(employees),
        'data': [dict(emp) for emp in employees]
    })

@app.route('/logs')
def get_logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 20').fetchall()
    conn.close()
    
    return jsonify({
        'total_logs': len(logs),
        'recent_logs': [dict(log) for log in logs]
    })

@app.route('/financial')
def get_financial():
    conn = get_db_connection()
    financial = conn.execute('SELECT * FROM financial_data ORDER BY created_at DESC').fetchall()
    conn.close()
    
    total_income = sum(f['amount'] for f in financial if f['transaction_type'] == 'INCOME')
    total_expense = sum(f['amount'] for f in financial if f['transaction_type'] == 'EXPENSE')
    
    return jsonify({
        'summary': {
            'total_income': total_income,
            'total_expense': abs(total_expense),
            'net_profit': total_income + total_expense
        },
        'transactions': [dict(fin) for fin in financial]
    })

@app.route('/sql_debug')
def sql_debug():
    """危險的 SQL 調試端點 - 允許直接執行 SQL 查詢"""
    query = request.args.get('query', '')
    
    if not query:
        return jsonify({
            'error': 'No query provided',
            'usage': '/sql_debug?query=SELECT * FROM employees',
            'warning': 'This endpoint allows direct SQL execution - USE WITH CAUTION'
        })
    
    try:
        conn = get_db_connection()
        result = conn.execute(query).fetchall()
        conn.close()
        
        return jsonify({
            'query': query,
            'result_count': len(result),
            'data': [dict(row) for row in result]
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'query': query
        }), 500

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': 'running',
        'database': 'connected'
    })

if __name__ == "__main__":
    init_internal_database()
    print("🔒 內部伺服器啟動中...")
    print("⚠️  此服務僅限內部訪問")
    print("📊 包含敏感的員工、財務和系統資料")
    print("🚨 SQL Debug 端點: /sql_debug?query=YOUR_QUERY")
    app.run(host="127.0.0.1", port=8080, debug=False)  # 只監聽 localhost
