# Libraries
import requests
from picamera import PiCamera
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
import Adafruit_CharLCD as LCD
import threading
import multiprocessing
import sys

# Camera
camera = PiCamera()
camera.resolution = (16*30, 9*30)#(1280,720)
#camera.framerate = 15
camera.rotation = 270

# LCD setup
lcd_rs        = 22
lcd_en        = 17
lcd_d4        = 26
lcd_d5        = 19
lcd_d6        = 13
lcd_d7        = 6
lcd_backlight = 4
lcd_columns   = 16
lcd_rows      = 2
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

# Buzzer config
buzzer = 23
GPIO.setup(buzzer, GPIO.OUT)
buzzerPWM = GPIO.PWM(buzzer, 400)
buzzerPWM.start(0)

# KeyPad config
rows = [24, 25, 12, 16]
cols = [4, 27, 18]

# KeyPad Class API
class KeyPad(object):
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

        for row in self.rows:
            GPIO.setup(row, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        for col in cols:
            GPIO.setup(col, GPIO.OUT)

        # map pin numberings to keypad
        self.keys = []
        self.keys.append(["1", "2", "3"])
        self.keys.append(["4", "5", "6"])
        self.keys.append(["7", "8", "9"])
        self.keys.append(["*", "0", "#"])

        # mask values for keys to prevent reading same input
        self.masked_keys = set([])

    # returns a string representing the input
    def read_input(self):
        input_ = None
        for col in cols:
            GPIO.output(col, GPIO.LOW)
            for row in rows:
                if not GPIO.input(row):
                    # key is pressed, check if already masked
                    if (col, row) not in self.masked_keys:
                        input_ = self.keys[rows.index(row)][cols.index(col)]
                        self.masked_keys.add((col, row))
                else:
                    # key is not pressed, remove from masked keys
                    if (col, row) in self.masked_keys:
                        self.masked_keys.remove((col, row))
            GPIO.output(col, GPIO.HIGH)
        return input_

    def wait_for_input(self, exitFlag, lock_flag, command, breakCode):
        # Blocking wait for input
        input_ = None
        while input_ is None:
            #print("lcd thread")
            if (exitFlag.FLAG) or (lock_flag.FLAG and command == 'lock') or (not lock_flag.FLAG and command == 'unlock'):
                return breakCode
            input_ = self.read_input()
            time.sleep(0.1)

        return input_

keyPad = KeyPad(rows, cols)

# Motion detector config
pir1 = 20
pir2 = 21

GPIO.setup(pir1, GPIO.IN) #Setup GPIO pin PIR as input
GPIO.setup(pir2, GPIO.IN) #Setup GPIO pin PIR as input
print ("Sensor initializing . . .")
time.sleep(2) #Give sensor time to startup
print("Sensors ready.")

# Servo lock config
LOCKSERVOPIN = 5
GPIO.setup(LOCKSERVOPIN, GPIO.OUT)
servo = GPIO.PWM(LOCKSERVOPIN, 50)
servo.start(0)

# Setup info
HOME_MESSAGE = 'Security system\n* to enter pass'

# Global variables

class ALERT_CLASS(object):
    def __init__(self):
        self.FLAG = False
        self.mv = multiprocessing.Value('i', 0)
    def set_on(self):
        self.FLAG = True
        self.mv.value = 1
    def set_off(self):
        self.FLAG = False
        self.mv.value = 0

INTRUDER_ALERT_ACTIVE = ALERT_CLASS()
DOOR_IS_LOCKED = ALERT_CLASS()

def securityMonitor(DOOR_IS_LOCKED, session, camera, lcd, pir1, pir2, buzzerPWM, filePath, sendImageIntruderURL, snapshotFilePath, sendSnapshotUrl, intruderOn, intruderOff, snapshot_delay, alarm_time):
    global INTRUDER_ALERT_ACTIVE
    global HOME_MESSAGE

    session.get(intruderOff)

    while True:
        print("security monitor thread")
        print(DOOR_IS_LOCKED.value)
        sys.stdout.flush()
        if (DOOR_IS_LOCKED.value):
            if (GPIO.input(pir1) and GPIO.input(pir2)):
                # intruder detected
                INTRUDER_ALERT_ACTIVE.FLAG = True
                # update lcd
                lcd.clear()
                lcd.message("INTRUDER\nALERT!")
                # sound the buzzer
                buzzerPWM.ChangeDutyCycle(50)
                # take snapshot
                camera.start_preview()
                camera.capture(filePath)
                camera.stop_preview()
                files = {'file' : ('intruder.jpeg', open(filePath, 'rb') ) }
                r = session.post(sendImageIntruderURL, files=files)
                session.get(intruderOn)
                time.sleep(alarm_time)
                buzzerPWM.ChangeDutyCycle(0)
                session.get(intruderOff)
                lcd.clear()
                lcd.message(HOME_MESSAGE)
                INTRUDER_ALERT_ACTIVE.FLAG = False
            else:
                camera.start_preview()
                camera.capture(snapshotFilePath)
                camera.stop_preview()

                files = {'file' : ('snapshot.jpeg', open(snapshotFilePath, 'rb') ) }
                r = session.post(sendSnapshotUrl, files=files)
                i = 0
                while True:
                    time.sleep(1.0/10)
                    i += 1.0/10
                    if (i >= snapshot_delay or ((GPIO.input(pir1) and GPIO.input(pir2)) and DOOR_IS_LOCKED.value)):
                        break
        #time.sleep(0.1)

def lockThread(session, keyPad, lcd, servo, getPassURL, getDoorStatusURL, postDoorOnURL, postDoorOffURL):
    global DOOR_IS_LOCKED
    global INTRUDER_ALERT_ACTIVE
    global HOME_MESSAGE

    lcd.clear()
    lcd.message(HOME_MESSAGE)
    while True:
        if INTRUDER_ALERT_ACTIVE.FLAG:
            time.sleep(0.5)
            continue

        if DOOR_IS_LOCKED.FLAG:
            lcd.clear()
            lcd.message(HOME_MESSAGE)
        else:
            lcd.clear()
            lcd.message("* to lock.")

        if DOOR_IS_LOCKED.FLAG:
            input_ = keyPad.wait_for_input(INTRUDER_ALERT_ACTIVE, DOOR_IS_LOCKED, 'unlock', "break")
            if (input_ == "break"):
                continue
            if (input_ == "*"):
                # start password entering mode
                lcd.clear()
                lcd.message("Enter PIN:")
                entered_password = ""
                stopSession = False
                while (len(entered_password) < 4):
                    lcd.clear()
                    lcd.message("Enter PIN:\n" + entered_password)
                    # get new input
                    input_ = keyPad.wait_for_input(INTRUDER_ALERT_ACTIVE, DOOR_IS_LOCKED, 'unlock', "break")
                    # check for breaks
                    if (input_ == "break"):
                        stopSession = True
                        break

                    try:
                        # check if input was number and add it to the entered password
                        cast = int(input_)
                        entered_password += input_
                    except ValueError:
                        # if *, quit password session. if #, remove the last character from entered password
                        if (input_ == "*"):
                            stopSession = True
                            break
                        elif (input_ == "#"):
                            if (len(entered_password) > 0):
                                entered_password = entered_password[:-1]

                if (stopSession):
                    continue

                # match password
                if (entered_password == session.get(getPassURL).text):
                    lcd.clear()
                    lcd.message("Opening vault")
                    # notify server that door is unlocked
                    session.get(postDoorOffURL)
                    while (DOOR_IS_LOCKED.FLAG):
                        time.sleep(0.5)
                    lcd.clear()
                    lcd.message("* to lock.")
        else:
            # door is open
            input_ = keyPad.wait_for_input(INTRUDER_ALERT_ACTIVE, DOOR_IS_LOCKED, 'lock', "break")
            if (input_ == "break"):
                time.sleep(0.5)
                continue
            if (input_ == "*"):
                # close vault
                lcd.clear()
                lcd.message("Closing vault")
                # notify server that door is locked
                session.get(postDoorOnURL)
                while (not DOOR_IS_LOCKED.FLAG):
                    time.sleep(0.5)

def serverDoorLock(session, getDoorStatusURL, postDoorOnURL, postDoorOffURL):
    global DOOR_IS_LOCKED

    while True:
        print("server thread")
        # check for server lock/unlock commands
        doorStatus = session.get(getDoorStatusURL).text
        if (DOOR_IS_LOCKED.FLAG and doorStatus == 'off'):
            print("unlocking door")
            # unlock door
            servo.ChangeDutyCycle(9.2)
            time.sleep(0.5)
            servo.ChangeDutyCycle(0)
            DOOR_IS_LOCKED.set_off()
        elif (not DOOR_IS_LOCKED.FLAG and doorStatus == 'on'):
            print("locking door")
            # lock door
            servo.ChangeDutyCycle(4)
            time.sleep(0.5)
            servo.ChangeDutyCycle(0)
            DOOR_IS_LOCKED.set_on()
        time.sleep(0.5)

HOME_URL = 'http://192.168.137.136:8080/'
session = requests.Session()

securityMonitorThread = threading.Thread(target=securityMonitor, args=(
    DOOR_IS_LOCKED.mv,
    session,
    camera,
    lcd,
    pir1,
    pir2,
    buzzerPWM,
    '/home/pi/Documents/intruder.jpeg',
    HOME_URL + 'sendIntruderImage/',
    '/home/pi/Documents/snapshot.jpeg',
    HOME_URL + 'sendImage/',
    HOME_URL + 'intruderOn',
    HOME_URL + 'intruderOff',
    5,
    10,
))

lockThread = threading.Thread(target=lockThread, args=(
    session,
    keyPad,
    lcd,
    servo,
    HOME_URL + 'getPassword',
    HOME_URL + 'getDoorStatus',
    HOME_URL + 'sendDoorStatusOn',
    HOME_URL + 'sendDoorStatusOff',
))

serverDoorLockThread = threading.Thread(target=serverDoorLock, args=(
    session,
    HOME_URL + 'getDoorStatus',
    HOME_URL + 'sendDoorStatusOn',
    HOME_URL + 'sendDoorStatusOff',
))

# start program
securityMonitorThread.start()
lockThread.start()
serverDoorLockThread.start()
