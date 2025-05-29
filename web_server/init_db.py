import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'web_database.db')

def clear_database():
    """清空資料庫中的所有資料"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 刪除所有留言
    cursor.execute("DELETE FROM comments")
    # 刪除所有用戶
    cursor.execute("DELETE FROM users")
    # 重置自動遞增計數器
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='comments'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
    
    conn.commit()
    conn.close()
    print("資料庫已清空！")

def drop_tables():
    """完全刪除所有表格"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS comments")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    conn.commit()
    conn.close()
    print("所有表格已刪除！")

def delete_database():
    """刪除整個資料庫檔案"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("資料庫檔案已刪除！")
    else:
        print("資料庫檔案不存在")

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

    # 插入一些測試留言
    cursor.execute("INSERT OR IGNORE INTO comments (username, message) VALUES (?, ?)",
                   ('admin', '今天是安全程式設計的報告日! 組合語言要讀不完了啦，拜託老師手下留情'))

    conn.commit()
    conn.close()
    print("資料庫初始化完成！")
    print("測試帳號:")
    print("- admin / adminpass")
    print("- user / userpass") 
    print("- test / testpass")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "clear":
            clear_database()
        elif command == "drop":
            drop_tables()
        elif command == "delete":
            delete_database()
        elif command == "reset":
            delete_database()
            init_database()
        else:
            print("可用指令:")
            print("python init_db.py clear   - 清空所有資料")
            print("python init_db.py drop    - 刪除所有表格")
            print("python init_db.py delete  - 刪除整個資料庫檔案")
            print("python init_db.py reset   - 重置資料庫(刪除後重建)")
    else:
        init_database()
