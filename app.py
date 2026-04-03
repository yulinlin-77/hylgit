from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

# 1. Initialize Flask application
app = Flask(__name__)

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
    # Get JSON data from frontend request
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
        # Create a new database connection for this request
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Start transaction to ensure data consistency
        db.start_transaction()

        # 1. Check if the booking exists
        cursor.execute("SELECT * FROM Bookings WHERE booking_id = %s", (booking_id,))
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # 2. Permission check: Only the owner can cancel their own booking
        if booking['customer_id'] != user_id:
            return jsonify({"error": "You can only cancel your own bookings"}), 403

        # 3. Status check: Only Confirmed/Pending can be cancelled
        if booking['status'] in ['Completed', 'Cancelled']:
            return jsonify({"error": f"Cannot cancel. Current status: {booking['status']}"}), 400

        # 4. Time check: Must cancel at least 24 hours in advance
        cursor.execute("SELECT * FROM Time_Slots WHERE slot_id = %s", (booking['slot_id'],))
        time_slot = cursor.fetchone()
        if not time_slot:
            return jsonify({"error": "Time slot not found"}), 404
        
        # The DATETIME from MySQL is already a datetime object, use it directly
        start_time = time_slot['start_time'] 
        now = datetime.now()

        if (start_time - now) < timedelta(hours=24):
            return jsonify({"error": "Cannot cancel within 24 hours of the appointment"}), 400

        # 5. Core operations: Update booking status + release time slot
        cursor.execute(
            "UPDATE Bookings SET status = 'Cancelled', cancel_reason = %s WHERE booking_id = %s",
            (cancel_reason, booking_id)
        )
        
        cursor.execute(
            "UPDATE Time_Slots SET is_available = TRUE WHERE slot_id = %s",
            (booking['slot_id'],)
        )

        # Commit transaction
        db.commit()
        return jsonify({"message": "Booking cancelled successfully, time slot released"}), 200

    except Error as db_err:
        # Handle database-specific errors
        if db and db.is_connected():
            db.rollback()
        return jsonify({"error": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        # Rollback on any error to prevent data corruption
        if db and db.is_connected():
            db.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

    finally:
        # Always close cursor and connection to release resources
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

# ==========================================
# 4. Start Flask service
# ==========================================
if __name__ == '__main__':
    print("🚀 Starting Flask service...")
    print("Service running at: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)