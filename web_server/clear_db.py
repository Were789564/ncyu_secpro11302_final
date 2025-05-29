import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'web_database.db')

def main():
    print("選擇清空方式:")
    print("1. 清空所有資料 (保留表格結構)")
    print("2. 刪除所有表格")
    print("3. 刪除整個資料庫檔案")
    print("4. 重置資料庫 (刪除後重建)")
    
    choice = input("請選擇 (1-4): ")
    
    if choice == "1":
        clear_data()
    elif choice == "2":
        drop_tables()
    elif choice == "3":
        delete_database()
    elif choice == "4":
        reset_database()
    else:
        print("無效選擇")

def clear_data():
    """清空所有資料但保留表格結構"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM comments")
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='comments'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
    
    conn.commit()
    conn.close()
    print("✅ 所有資料已清空，表格結構保留")

def drop_tables():
    """刪除所有表格"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS comments")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    conn.commit()
    conn.close()
    print("✅ 所有表格已刪除")

def delete_database():
    """刪除整個資料庫檔案"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("✅ 資料庫檔案已刪除")
    else:
        print("❌ 資料庫檔案不存在")

def reset_database():
    """重置資料庫"""
    delete_database()
    # 重新創建資料庫
    from init_db import init_database
    init_database()
    print("✅ 資料庫已重置")

if __name__ == "__main__":
    main()
