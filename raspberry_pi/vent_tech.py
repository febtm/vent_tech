from imutils.video import VideoStream
from imutils.video import FPS
from multiprocessing import Process
from multiprocessing import Queue

import numpy as np
import imutils
import time
import datetime
import cv2

import RPi.GPIO as GPIO
import http.client, urllib.parse
import serial


arduino = serial.Serial('/dev/ttyACM0', 9600)

cloudKey = 'YX19C42D8TWRKEFY'


stepper_1 = 2
stepper_2 = 3
stepper_3 = 4
stepper_4 = 17

stepper_sleep_time = 0.001

stepper_full_steps = 25
stepper_half_steps = 13
stepper_one_step = 1
stepper_current_step = 0

outlet_fan = 27


print("Loading up Skyfall !!!")

CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]

net = cv2.dnn.readNetFromCaffe("library.txt", "library.caffemodel")

inputQueue = Queue(maxsize=1)
outputQueue = Queue(maxsize=1)

detections = None
personCount = 0
co2Level = 0.0

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(stepper_1, GPIO.OUT)
GPIO.setup(stepper_2, GPIO.OUT)
GPIO.setup(stepper_3, GPIO.OUT)
GPIO.setup(stepper_4, GPIO.OUT)

GPIO.setup(outlet_fan, GPIO.OUT)

GPIO.output(outlet_fan, GPIO.HIGH)


def classifyFrame(net, inputQueue, outputQueue):
	
	while True:
	
		if not inputQueue.empty():
			
			frame = inputQueue.get()
			frame = cv2.resize(frame, (300, 300))
			blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)

			net.setInput(blob)
			detections = net.forward()

			outputQueue.put(detections)


def getPersonCount():

        frame = vs.read()
        frame = imutils.resize(frame, width=640)
        (fH, fW) = frame.shape[:2]

        detections = None

        pc = 0
        
        if inputQueue.empty():
                inputQueue.put(frame)

        if not outputQueue.empty():
                detections = outputQueue.get()

        if detections is not None:
                
                for i in np.arange(0, detections.shape[2]):
                        
                        confidence = detections[0, 0, i, 2]

                        if confidence < 0.2:
                                continue

                        idx = int(detections[0, 0, i, 1])

                        if CLASSES[idx] is "person":
                                pc += 1

        print("----- In Get Person Count, pc is ", pc)

        return pc


def getCO2Level():
        
        co2_level = [0]
        
        co2_level[0] = 0.0
        
        while (co2_level[0] is 0.0):
                
                co2_level[0] = float (arduino.readline())
                
                if (co2_level[0] > 2000.0):
                        co2_level[0] = 0.0
                        
        print("\n----- In Get CO2 Level, co2_level[0] is ", co2_level[0])
        
        return co2_level[0]


def sendToCloud(pc, co2, stepper_current_step):

        time.sleep(5)

        params = urllib.parse.urlencode({'field1': pc, 'field2': co2, 'field3': stepper_current_step, 'key':cloudKey })
        headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
        conn = http.client.HTTPConnection("api.thingspeak.com:80")

        try:
                conn.request("POST", "/update", params, headers)
                response = conn.getresponse()
                print("\n----- Data sent to Cloud !")
                data = response.read()
                conn.close()

        except:
                print("\n----- Data not sent - No Network Connection !")

                
def setStepperMotor(a, b, c, d):

        GPIO.output(stepper_1, a)
        GPIO.output(stepper_2, b)
        GPIO.output(stepper_3, c)
        GPIO.output(stepper_4, d)


def moveStepperClockWise(step_difference):

        time.sleep(5)
        
        for i in range (0, step_difference):

                setStepperMotor(0, 1, 0, 0)
                time.sleep(stepper_sleep_time)
                
                setStepperMotor(0, 1, 0, 1)
                time.sleep(stepper_sleep_time)
                
                setStepperMotor(0, 0, 0, 1)
                time.sleep(stepper_sleep_time)
                
                setStepperMotor(1, 0, 0, 1)
                time.sleep(stepper_sleep_time)
                
                setStepperMotor(1, 0, 0, 0)
                time.sleep(stepper_sleep_time)
                
                setStepperMotor(1, 0, 1, 0)
                time.sleep(stepper_sleep_time)
                
                setStepperMotor(0, 0, 1, 0)
                time.sleep(stepper_sleep_time)
                
                setStepperMotor(0, 1, 1, 0)
                time.sleep(stepper_sleep_time)


p = Process(target=classifyFrame, args=(net, inputQueue, outputQueue,))
p.daemon = True
p.start()

vs = VideoStream(usePiCamera=True).start()
time.sleep(2)
fps = FPS().start()


while True:

        print("\n\n***** START OF LOOP *****")

        co2Level = getCO2Level()

        personCount = getPersonCount()

        if (personCount == 0):

                print("\n1. Person Count is 0, in Loop 1")

                if (co2Level > 1400.0):

                        if (stepper_current_step < stepper_half_steps):
                                moveStepperClockWise(stepper_half_steps - stepper_current_step)

                        stepper_current_step = stepper_half_steps
                        
                        print ("2. In Loop 1, Stepper Current Step is ", stepper_current_step)

                else:
                        
                        if (stepper_current_step > 0):
                                moveStepperClockWise(stepper_full_steps - stepper_current_step)

                        print ("2. Stepper Current Step is 0, in Loop 1")
				
                        stepper_current_step = 0

        if(personCount > 0):

                print("\n1. In Loop 2, Person Count is ", personCount)

                if (co2Level > 1400.0):

                        if (stepper_current_step < stepper_half_steps):
                                moveStepperClockWise(stepper_half_steps - stepper_current_step)

                        stepper_current_step = stepper_half_steps

                        print ("2. In Loop 2, Stepper Current Step is ", stepper_current_step)

                else:

                        go_to_step = 0
                        
                        if (personCount == 1):
                                go_to_step = 2

                        elif (personCount == 2):
                                go_to_step = 4

                        elif (personCount == 3):
                                go_to_step = 6

                        elif (personCount == 4):
                                go_to_step = 8

                        else:
                                go_to_step = stepper_half_steps

                        if(stepper_current_step < go_to_step):
                                moveStepperClockWise(go_to_step - stepper_current_step)

                        elif (stepper_current_step > go_to_step):
                                moveStepperClockWise((stepper_full_steps - stepper_current_step) + go_to_step)

                        stepper_current_step = go_to_step
                        
                        print ("2. In Loop 2, Stepper Current Step is ", stepper_current_step)

        fps.update()
        
        sendToCloud(personCount, co2Level, stepper_current_step)

        time.sleep(5)

fps.stop()

GPIO.cleanup()

cv2.destroyAllWindows()
vs.stop()
