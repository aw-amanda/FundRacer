from gevent import monkey
monkey.patch_all(thread=False)
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import socket
import os
import sys
import webbrowser
import signal
import atexit
import time
import psutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Determine the base path for bundled files
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

# Define paths for templates and static files
templates_folder = os.path.join(base_path, 'templates')
static_folder = os.path.join(base_path, 'static')

# Initialize Flask app with custom template and static folders
app = Flask(__name__, template_folder=templates_folder, static_folder=static_folder)

# Initialize SocketIO with async_mode="gevent"
socketio = SocketIO(app, async_mode="gevent")

# Initialize funds with starting values
funds = {
    "Fund Name 1": 0,
    "Fund Name 2": 0,
    "Fund Name 3": 0,
    "Fund Name 4": 0
}

global_goal = 10000  # Default global goal set to 10000

# Define a dedicated data directory
DATA_DIR = os.path.join(base_path, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# File to store donation history
DONATION_HISTORY_FILE = os.path.join(DATA_DIR, "donation_history.txt")

# Buffer to store donations temporarily
donation_buffer = []

# Function to flush the buffer to the file
def flush_donation_buffer():
    if donation_buffer:
        try:
            with open(DONATION_HISTORY_FILE, "a") as file:
                for donation in donation_buffer:
                    file.write(f"{donation['donor']}, {donation['amount']}, {donation['fund']}\n")
            donation_buffer.clear()
        except Exception as e:
            logging.error(f"Error writing to donation history file: {e}")

# Reset funds event handler
@socketio.on('reset_funds')
def handle_reset_funds():
    global funds
    funds = {key: 0 for key in funds}  # Reset all funds to 0
    logging.info("Funds reset: %s", funds)

    # Emit the updated funds to all connected clients in the /progress namespace
    socketio.emit('fund_progress', {'funds': funds, 'global_goal': global_goal}, namespace='/progress')

@app.route('/')
def input_page():
    return render_template('input.html')

# Default namespace for input.html
@socketio.on('message', namespace='/')
def handle_message(message):
    logging.info("Received message: %s", message)
    emit('response', {'data': 'Message from input.html'})

@app.route('/progress')
def progress_page():
    return render_template('progress.html')

# Namespace for progress.html
@socketio.on('message', namespace='/progress')
def handle_progress(message):
    logging.info("Received message in progress: %s", message)
    emit('response', {'data': 'Message from progress.html'})

# Read donation history and restore funds
def restore_funds():
    global funds
    try:
        with open(DONATION_HISTORY_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    donor, amount, fund = line.split(", ")
                    if fund not in funds:
                        logging.warning(f"Invalid fund in history: {fund}. Skipping line.")
                        continue
                    funds[fund] += float(amount)
                except ValueError as e:
                    logging.error(f"Skipping malformed line: {line}. Error: {e}")
        logging.info("Restored funds from history: %s", funds)
    except FileNotFoundError:
        logging.info("No donation history found. Starting with fresh funds.")

    # Clear the donation history file for the new session
    open(DONATION_HISTORY_FILE, "w").close()

# Call the function to restore funds when the application starts
restore_funds()

# Route to set the global goal
@app.route("/set_global_goal", methods=["POST"])
def set_global_goal():
    data = request.get_json()
    goal = float(data.get("goal"))

    global global_goal
    global_goal = goal
    logging.info(f"Updated global goal: {global_goal}")
    return {"status": "success", "message": f"Global goal updated to {goal}"}

@socketio.on('new_donation')
def handle_new_donation(data):
    try:
        donor = str(data['donor'])
        amount = float(data['amount'])
        fund = str(data['fund'])

        if fund not in funds:
            raise ValueError("Invalid fund selected.")

        funds[fund] += amount
        logging.info(f"Emitting updated funds: {funds}")

        # Add donation to the buffer
        donation_buffer.append({'donor': donor, 'amount': amount, 'fund': fund})

        # Flush the buffer to the file every 10 donations
        if len(donation_buffer) >= 10:
            flush_donation_buffer()

        socketio.emit('fund_progress', {'funds': funds, 'global_goal': global_goal}, namespace='/progress')
        socketio.emit('donation_success', {'message': 'Donation submitted successfully!'})

        donation_message = f"{donor} donated ${amount} to {fund}!"
        logging.info(f"Emitting donation message: {donation_message}")
        socketio.emit('donation_message', {'message': donation_message}, namespace='/progress')
    except (KeyError, ValueError) as e:
        logging.error(f"Invalid donation data: {data}. Error: {e}")
        socketio.emit('donation_error', {'message': 'Invalid donation data.'})

# Function to shut down the server
def shutdown_server():
    logging.info("Shutting down server...")
    flush_donation_buffer()  # Ensure all donations are saved
    socketio.stop()

# Route to handle shutdown from the HTML button
@app.route("/shutdown", methods=["POST"])
def shutdown():
    shutdown_server()
    return "Server shutting down..."

# Cleanup function using atexit
@atexit.register
def on_exit():
    flush_donation_buffer()
    logging.info("Server has been shut down.")

# Function to check if a port is in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Terminate the previous instance if the port is in use
def terminate_previous_instance(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    logging.info(f"Terminating previous instance (PID: {proc.pid})...")
                    proc.terminate()
                    proc.wait()
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

if is_port_in_use(5000):
    logging.info("Port 5000 is already in use. Terminating the previous instance...")
    terminate_previous_instance(5000)

if __name__ == '__main__':
    logging.info("Starting server...")
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        time.sleep(2)  # Wait for the server to start
        webbrowser.open('http://localhost:5000/')
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)