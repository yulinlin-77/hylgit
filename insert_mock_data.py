import mysql.connector
from datetime import datetime, timedelta

print("🔧 Inserting test data into the database...")

try:
    # Connect to the database (replace 123456 with your actual password)
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456", 
        database="booking_system"
    )
    cursor = db.cursor()

    # 1. Create a test customer (user_id will be 1)
    cursor.execute("""
        INSERT INTO Users (username, password_hash, role) 
        VALUES ('test_customer', 'hashed_pwd', 'Customer')
    """)
    customer_id = cursor.lastrowid
    print(f"✅ Customer created successfully, ID: {customer_id}")

    # 2. Create a test specialist (user_id = 2) and specialist profile (specialist_id = 1)
    cursor.execute("""
        INSERT INTO Users (username, password_hash, role) 
        VALUES ('test_expert', 'hashed_pwd', 'Specialist')
    """)
    expert_user_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO Specialists (user_id, expertise_area, fee) 
        VALUES (%s, 'IT Consulting', 500.00)
    """, (expert_user_id,))
    specialist_id = cursor.lastrowid
    print(f"✅ Specialist created successfully, Profile ID: {specialist_id}")

    # 3. Create a time slot (3 days from now, so > 24h for cancellation test)
    # Set is_available = FALSE because it will be booked
    start_time = datetime.now() + timedelta(days=3)
    end_time = start_time + timedelta(hours=1)
    
    cursor.execute("""
        INSERT INTO Time_Slots (specialist_id, start_time, end_time, is_available) 
        VALUES (%s, %s, %s, FALSE)
    """, (specialist_id, start_time, end_time))
    slot_id = cursor.lastrowid
    print(f"✅ Time slot created successfully, ID: {slot_id}, Time: {start_time.strftime('%Y-%m-%d %H:%M')}")

    # 4. Create a confirmed booking (booking_id will be 1)
    cursor.execute("""
        INSERT INTO Bookings (customer_id, slot_id, status, total_price, cancel_reason) 
        VALUES (%s, %s, 'Confirmed', 500.00, NULL)
    """, (customer_id, slot_id))
    booking_id = cursor.lastrowid
    print(f"✅ Booking created successfully, Booking ID: {booking_id}")

    # Commit all changes to the database
    db.commit()
    print("🎉 All test data inserted successfully! You can now test the cancellation API.")

except Exception as e:
    db.rollback()
    print(f"❌ Data insertion failed: {e}")

finally:
    if 'cursor' in locals(): cursor.close()
    if 'db' in locals(): db.close()