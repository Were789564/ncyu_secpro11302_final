import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 建立 users 資料表
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT
)
''')

# 插入測試資料
cursor.execute("INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)",('admin', 'adminpass', 'admin@example.com'))

conn.commit()
conn.close()

print("資料庫與 users 表建立完成，並已插入測試用使用者")
