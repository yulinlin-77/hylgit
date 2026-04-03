from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

# 1. Initialize Flask application
app = Flask(__name__)

# 测试路由：确认Flask正常工作
@app.route('/')
def hello():
    return "Flask is working! Hello from backend!"

# 2. Define a function to get a new database connection for each request
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",  # Make sure this is your actual MySQL password
        database="booking_system"
    )

# ==========================================
# 3. Core: Cancel Booking API
# ==========================================
@app.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is empty"}), 400
    
    user_id = data.get('user_id')
    cancel_reason = data.get('cancel_reason')

    if not user_id or not cancel_reason:
        return jsonify({"error": "Missing required parameters"}), 400

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        db.start_transaction()

        cursor.execute("SELECT * FROM Bookings WHERE booking_id = %s", (booking_id,))
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        if booking['customer_id'] != user_id:
            return jsonify({"error": "You can only cancel your own bookings"}), 403

        if booking['status'] in ['Completed', 'Cancelled']:
            return jsonify({"error": f"Cannot cancel. Current status: {booking['status']}"}), 400

        cursor.execute("SELECT * FROM Time_Slots WHERE slot_id = %s", (booking['slot_id'],))
        time_slot = cursor.fetchone()
        if not time_slot:
            return jsonify({"error": "Time slot not found"}), 404
        
        start_time = time_slot['start_time'] 
        now = datetime.now()

        if (start_time - now) < timedelta(hours=24):
            return jsonify({"error": "Cannot cancel within 24 hours of the appointment"}), 400

        cursor.execute(
            "UPDATE Bookings SET status = 'Cancelled', cancel_reason = %s WHERE booking_id = %s",
            (cancel_reason, booking_id)
        )
        
        cursor.execute(
            "UPDATE Time_Slots SET is_available = TRUE WHERE slot_id = %s",
            (booking['slot_id'],)
        )

        db.commit()
        return jsonify({"message": "Booking cancelled successfully, time slot released"}), 200

    except Error as db_err:
        if db and db.is_connected():
            db.rollback()
        return jsonify({"error": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        if db and db.is_connected():
            db.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

# ==========================================
# 4. Core: Reschedule Booking API (终于加上了！)
# ==========================================
@app.route('/api/bookings/<int:booking_id>/reschedule', methods=['POST'])
def reschedule_booking(booking_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is empty"}), 400
    
    user_id = data.get('user_id')
    new_slot_id = data.get('new_slot_id')

    if not user_id or not new_slot_id:
        return jsonify({"error": "Missing required parameters (user_id or new_slot_id)"}), 400

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        db.start_transaction()

        cursor.execute("SELECT * FROM Bookings WHERE booking_id = %s", (booking_id,))
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking['customer_id'] != user_id:
            return jsonify({"error": "You can only modify your own bookings"}), 403
        if booking['status'] in ['Completed', 'Cancelled']:
            return jsonify({"error": f"Cannot reschedule. Current status: {booking['status']}"}), 400

        old_slot_id = booking['slot_id']
        if old_slot_id == new_slot_id:
            return jsonify({"message": "New time slot is the same as current, no change needed"}), 200

        cursor.execute("SELECT * FROM Time_Slots WHERE slot_id = %s", (old_slot_id,))
        old_time_slot = cursor.fetchone()
        
        start_time = old_time_slot['start_time']
        now = datetime.now()
        if (start_time - now) < timedelta(hours=24):
            return jsonify({"error": "Cannot reschedule within 24 hours of the original booking"}), 400

        cursor.execute("SELECT * FROM Time_Slots WHERE slot_id = %s", (new_slot_id,))
        new_time_slot = cursor.fetchone()
        if not new_time_slot:
            return jsonify({"error": "Target time slot does not exist"}), 404
            
        if not new_time_slot['is_available']:
            return jsonify({"error": "This time slot was just taken by another user"}), 409

        cursor.execute(
            "UPDATE Time_Slots SET is_available = TRUE WHERE slot_id = %s",
            (old_slot_id,)
        )
        
        cursor.execute(
            "UPDATE Time_Slots SET is_available = FALSE WHERE slot_id = %s",
            (new_slot_id,)
        )

        cursor.execute(
            "UPDATE Bookings SET slot_id = %s WHERE booking_id = %s",
            (new_slot_id, booking_id)
        )

        db.commit()
        return jsonify({"message": "Booking rescheduled successfully!"}), 200

    except Error as db_err:
        if db and db.is_connected():
            db.rollback()
        return jsonify({"error": f"Database error: {str(db_err)}"}), 500
    except Exception as e:
        if db and db.is_connected():
            db.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

# ==========================================
# 5. Start Flask service
# ==========================================
if __name__ == '__main__':
    print("🚀 Starting Flask service...")
    print("Service running at: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)