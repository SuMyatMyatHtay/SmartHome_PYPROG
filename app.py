
import time
import datetime
import csv
import RPi.GPIO as GPIO
import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

GPIO.setmode(GPIO.BCM)
LED_PIN = 24
GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)

aircon_state_data_file = "/home/pi/Desktop/sec_python_project_final/csvfiles/aircon_state_data.csv"
total_usage_data_file = "/home/pi/Desktop/sec_python_project_final/csvfiles/total_usage_data.csv"
desired_usage_data_file = "/home/pi/Desktop/sec_python_project_final/csvfiles/desired_usage_data.csv"


led_state = False
prev_led_state = False
current_date = datetime.date.today()

desired_usage_time = 0
remaining_usage = 0

# Telegram bot token and chat ID 
TELEGRAM_BOT_TOKEN = '6602018762:AAF9F1p3YjtTyjzou1AB3Zy3wwKOmRZaLFo'
TELEGRAM_CHAT_ID = '1607213208'

def record_led_state_change(state):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(aircon_state_data_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, 'ON' if state else 'OFF'])

def save_total_usage(total_usage):
    today = datetime.date.today().strftime("%Y-%m-%d")
    with open(total_usage_data_file, "a", newline="") as f:
        writer = csv.writer(f)
        # Convert total usage to hours, minutes, and seconds
        total_usage_hours = total_usage // 3600
        total_usage_minutes = (total_usage % 3600) // 60
        total_usage_seconds = total_usage % 60
        writer.writerow([today, total_usage_hours, total_usage_minutes, total_usage_seconds])

def save_desired_usage(desired_usage_hours, desired_usage_minutes):
    total_minutes = desired_usage_hours * 60 + desired_usage_minutes
    with open(desired_usage_data_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([total_minutes])

def load_desired_usage():
    try:
        with open(desired_usage_data_file, "r") as f:
            reader = csv.reader(f)
            desired_usage = next(reader)
            return int(desired_usage[0])
    except (FileNotFoundError, StopIteration):
        return 0

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/current_total_usage')
def current_total_usage():
    total_usage_seconds = get_led_usage_today()
    return jsonify(total_usage=total_usage_seconds)


@app.route('/turn_on')
def turn_on_led():
    global led_state
    if not led_state:
        led_state = True
        record_led_state_change(True)
        GPIO.output(LED_PIN, GPIO.HIGH)  # Turn on the LED
        return jsonify(success=True)
    return jsonify(success=False)

@app.route('/turn_off')
def turn_off_led():
    global led_state
    if led_state:
        led_state = False
        record_led_state_change(False)
        GPIO.output(LED_PIN, GPIO.LOW)  # Turn off the LED
        return jsonify(success=True)
    return jsonify(success=False)

@app.route('/total_usage')
def total_usage():
    global current_date, desired_usage_time

    # Check if a new day has started
    if current_date != datetime.date.today():
        total_usage_seconds = get_led_usage_today()
        save_total_usage(total_usage_seconds)
        current_date = datetime.date.today()

    total_usage_seconds = get_led_usage_today()
    print(total_usage_seconds);
    total_usage_hours = total_usage_seconds // 3600
    total_usage_minutes = (total_usage_seconds % 3600) // 60
    total_usage_second = total_usage_seconds % 60

    # Load the desired usage time from the file
    desired_usage_time = load_desired_usage()
    print(desired_usage_time )
    # Calculate remaining usage time in seconds
    remaining_usage_sec = max(desired_usage_time * 60 - total_usage_seconds, 0)
    remaining_hours = remaining_usage_sec // 3600

    remaining_minutes = (remaining_usage_sec % 3600) //60
    remaining_seconds = remaining_usage_sec % 60

    desired_usage_time_seconds = desired_usage_time * 60
    desired_usage_time_hours = desired_usage_time_seconds // 3600
    desired_usage_time_minutes = (desired_usage_time_seconds % 3600) //60

    return jsonify(
        hours=total_usage_hours,
        minutes=total_usage_minutes,
        seconds=total_usage_second,
        remaining_hours=remaining_hours,
        remaining_minutes=remaining_minutes,
        remaining_seconds=remaining_seconds, 
        desired_usage_hours=desired_usage_time_hours,
        desired_usage_minutes=desired_usage_time_minutes

    )


@app.route('/set_desired_usage', methods=['POST'])
def set_desired_usage():
    global desired_usage_time
    data = request.get_json()
    desired_hours = int(data.get('desired_hours', 0))
    desired_minutes = int(data.get('desired_minutes', 0))
    total_desired_minutes = desired_hours * 60 + desired_minutes
    save_desired_usage(desired_hours, desired_minutes)
    desired_usage_time = total_desired_minutes  # Update desired_usage_time in minutes
    return jsonify(success=True)

def get_led_usage_today():
    today = datetime.date.today().strftime("%Y-%m-%d")
    total_usage = 0

    with open(aircon_state_data_file, "r", newline="") as f:
        reader = csv.reader(f)
        lines = list(reader)

    for i in range(len(lines) - 1):
        entry, state = lines[i]

        if entry.startswith(today) and state == "ON" and lines[i + 1][1] == "OFF":
            entry_time = datetime.datetime.strptime(entry, "%Y-%m-%d %H:%M:%S")
            next_entry_time = datetime.datetime.strptime(lines[i + 1][0], "%Y-%m-%d %H:%M:%S")
            duration = (next_entry_time - entry_time).seconds
            total_usage += duration

    return total_usage


@app.route('/send_telegram_message', methods=['POST'])
def send_telegram_message():
    data = request.get_json()
    bot_token = data.get('bot_token', '')
    chat_id = data.get('chat_id', '')
    message = data.get('message', '')

    if bot_token and chat_id:
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        response = requests.post(url, data={'chat_id': chat_id, 'text': message})
        return jsonify(success=True)
    else:
        return jsonify(success=False, error='Bot token and chat ID are required.')



if __name__ == '__main__':
    app.run(debug=True)
