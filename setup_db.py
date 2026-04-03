import mysql.connector
from datetime import datetime, timedelta

print("🚀 开始一键初始化数据库、建表并注入数据...")

try:
    # 1. 连上本地 MySQL（暂时不指定 database）
    db = mysql.connector.connect(host="localhost", user="root", password="123456")
    cursor = db.cursor()

    # 2. 强行创建数据库！
    cursor.execute("CREATE DATABASE IF NOT EXISTS booking_system;")
    cursor.execute("USE booking_system;")
    print("✅ 数据库 booking_system 成功创建并选中！")

    # 3. 创建四大核心表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('Admin','Customer','Specialist') NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Specialists (
            specialist_id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            expertise_area VARCHAR(100) NOT NULL,
            fee DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Time_Slots (
            slot_id INT PRIMARY KEY AUTO_INCREMENT,
            specialist_id INT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            is_available BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (specialist_id) REFERENCES Specialists(specialist_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Bookings (
            booking_id INT PRIMARY KEY AUTO_INCREMENT,
            customer_id INT NOT NULL,
            slot_id INT NOT NULL UNIQUE,
            status ENUM('Pending','Confirmed','Cancelled','Completed') NOT NULL,
            total_price DECIMAL(10,2) NOT NULL,
            cancel_reason TEXT NULL,
            FOREIGN KEY (customer_id) REFERENCES Users(user_id),
            FOREIGN KEY (slot_id) REFERENCES Time_Slots(slot_id)
        )
    """)
    print("✅ 四大核心表建表成功！")

    # 4. 清理旧数据，防止重复报错
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE Bookings;")
    cursor.execute("TRUNCATE TABLE Time_Slots;")
    cursor.execute("TRUNCATE TABLE Specialists;")
    cursor.execute("TRUNCATE TABLE Users;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # 5. 注入绝对匹配的假数据
    cursor.execute("INSERT INTO Users (user_id, username, password_hash, role) VALUES (1, 'customer1', 'pwd', 'Customer')")
    cursor.execute("INSERT INTO Users (user_id, username, password_hash, role) VALUES (2, 'expert1', 'pwd', 'Specialist')")
    cursor.execute("INSERT INTO Specialists (specialist_id, user_id, expertise_area, fee) VALUES (1, 2, 'IT', 500.0)")
    
    # 建一个3天后的可用时间槽
    start_time = datetime.now() + timedelta(days=3)
    end_time = start_time + timedelta(hours=1)
    cursor.execute("INSERT INTO Time_Slots (slot_id, specialist_id, start_time, end_time, is_available) VALUES (1, 1, %s, %s, FALSE)", (start_time, end_time))
    
    # 建一个 booking_id 为 1 的订单，属于 user_id 1
    cursor.execute("INSERT INTO Bookings (booking_id, customer_id, slot_id, status, total_price) VALUES (1, 1, 1, 'Confirmed', 500.0)")

    db.commit()
    print("🎉 假订单注入完毕！地基彻底打好！")

except Exception as e:
    print(f"❌ 发生致命错误: {e}")
finally:
    if 'cursor' in locals() and cursor: cursor.close()
    if 'db' in locals() and db.is_connected(): db.close()
    