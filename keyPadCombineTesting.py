import RPi.GPIO as GPIO
import time
import I2C_LCD_driver  # Replace with the correct import for your LCD library
import subprocess
from time import sleep 

GPIO.setmode(GPIO.BCM) #choose BCM mode, refer to pins as GPIO no.
GPIO.setwarnings(False)
GPIO.setup(24,GPIO.OUT) 


MATRIX = [[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9],
          ['*', 0, '#']]  # layout of keys on keypad
ROW = [6, 20, 19, 13]  # row pins
COL = [12, 5, 16]  # column pins

# Set column pins as outputs, and write default value of 1 to each
for i in range(3):
    GPIO.setup(COL[i], GPIO.OUT)
    GPIO.output(COL[i], 1)

# Set row pins as inputs, with pull up
for j in range(4):
    GPIO.setup(ROW[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize the LCD screen
lcd = I2C_LCD_driver.lcd()  # Replace with the initialization code for your LCD library

# Initialize the buzzer
BUZZER_PIN = 18 # Replace with the GPIO pin number connected to the buzzer
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.output(BUZZER_PIN, GPIO.LOW)

entered_numbers = ''  # String to store the entered numbers
wrong_attempts = 0 

# Function to activate the buzzer for a specified duration
def activate_buzzer(duration):
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def run_turn_on_camera():
    subprocess.Popen(["python3", "takePhotoIfUnknown.py"])

# Scan keypad
while True:
    GPIO.output(24,0); 
    for i in range(3):  # loop thru’ all columns
        GPIO.output(COL[i], 0)  # pull one column pin low
        for j in range(4):  # check which row pin becomes low
            if GPIO.input(ROW[j]) == 0:  # if a key is pressed
                key_pressed = MATRIX[j][i]
                print(key_pressed)  # print the key pressed
                while GPIO.input(ROW[j]) == 0:  # debounce
                    time.sleep(0.1)

                # Check for special keys
                if key_pressed == '*':
                    # Backspace functionality
                    if len(entered_numbers) > 0:
                        entered_numbers = entered_numbers[:-1]  # Remove the last character
                elif key_pressed == '#':
                    # Check if the entered number is "1234"
                    if entered_numbers == '1234':
                        GPIO.output(24,1)
                        sleep(2); 
                        print("Door unlock")
                        wrong_attempts = 0
                    else:
                        GPIO.output(24,0)
                        print("Thief Thief")
                        wrong_attempts += 1 
                        activate_buzzer(3)  # Activate the buzzer for 3 seconds
                        if wrong_attempts >= 3:
                            run_turn_on_camera()  # Run turnOnCamera.py after 3 consecutive wrong attempts
                            wrong_attempts = 0
                    entered_numbers = ''  # Clear the entered_numbers string for the next input
                else:
                    # Update the entered numbers string
                    entered_numbers += str(key_pressed)

                # Display the entered numbers on the LCD screen
                lcd.lcd_clear()  # Clear the screen
                lcd.lcd_display_string(entered_numbers, 1)  # Display the entered numbers on line 1

        GPIO.output(COL[i], 1)  # write back default value of 1
