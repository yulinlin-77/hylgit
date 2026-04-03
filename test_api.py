import requests

# Your local backend address, assuming you cancel the order with booking_id = 1
url = "http://127.0.0.1:5000/api/bookings/1/cancel"

# Simulate JSON data sent from the frontend
# (You need to ensure that user_id=1 and booking_id=1 exist in the database)
payload = {
    "user_id": 1,
    "cancel_reason": "I have something urgent and must cancel this appointment"
}

print(f"Sending cancellation request to {url}...")
# Send POST request
response = requests.post(url, json=payload)

# Print backend response
print(f"Status code: {response.status_code}")
print(f"Backend response: {response.json()}")