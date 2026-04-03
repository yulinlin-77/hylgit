-- 1. 用户表 (Users)
CREATE TABLE Users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('Admin','Customer','Specialist') NOT NULL
);

-- 2. 专家详情表 (Specialists)
CREATE TABLE Specialists (
    specialist_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    expertise_area VARCHAR(100) NOT NULL,
    fee DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- 3. 时间槽表 (Time_Slots)
CREATE TABLE Time_Slots (
    slot_id INT PRIMARY KEY AUTO_INCREMENT,
    specialist_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (specialist_id) REFERENCES Specialists(specialist_id)
);

-- 4. 预约订单表 (Bookings)
CREATE TABLE Bookings (
    booking_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    slot_id INT NOT NULL UNIQUE, -- 强制一个时间槽只能被订一次
    status ENUM('Pending','Confirmed','Cancelled','Completed') NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    cancel_reason TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Users(user_id),
    FOREIGN KEY (slot_id) REFERENCES Time_Slots(slot_id)
);
