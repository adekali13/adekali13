import RPi.GPIO as GPIO
import time
import time
import cv2
import numpy as np
from tensorflow.lite.python.interpreter import Interpreter


# Configuration des pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)


def detect():
    modelpath = 'detect.tflite'
    lblpath = 'labelmap.txt'
    min_conf = 0.5
    # cap = cv2.VideoCapture('demo.mp4')
    cap = cv2.VideoCapture(0)
    interpreter = Interpreter(model_path=modelpath)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    float_input = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    with open(lblpath, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    while (True):
        ret, frame = cap.read()
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imH, imW, _ = frame.shape
        image_resized = cv2.resize(image_rgb, (width, height))
        input_data = np.expand_dims(image_resized, axis=0)
        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if float_input:
            input_data = (np.float32(input_data) - input_mean) / input_std

        # Perform the actual detection by running the model with the image as input
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

        boxes = interpreter.get_tensor(output_details[1]['index'])[0]  # Bounding box coordinates of detected objects
        classes = interpreter.get_tensor(output_details[3]['index'])[0]  # Class index of detected objects
        scores = interpreter.get_tensor(output_details[0]['index'])[0]  # Confidence of detected objects

        detections = []

        for i in range(len(scores)):
            if ((scores[i] > min_conf) and (scores[i] <= 1.0)):
                # Get bounding box coordinates and draw box
                # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
                ymin = int(max(1, (boxes[i][0] * imH)))
                xmin = int(max(1, (boxes[i][1] * imW)))
                ymax = int(min(imH, (boxes[i][2] * imH)))
                xmax = int(min(imW, (boxes[i][3] * imW)))
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)
                # Draw label
                object_name = labels[int(classes[i])]  # Look up object name from "labels" array using class index
                label = '%s: %d%%' % (object_name, int(scores[i] * 100))  # Example: 'person: 72%'
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size
                label_ymin = max(ymin, labelSize[1] + 10)  # Make sure not to draw label too close to top of window
                cv2.rectangle(frame, (xmin, label_ymin - labelSize[1] - 10),
                              (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255),
                              cv2.FILLED)  # Draw white box to put label text in
                cv2.putText(frame, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0),
                            2)  # Draw label text
                detections.append([object_name, scores[i], xmin, ymin, xmax, ymax])

        cv2.imshow('output', frame)
        if (cv2.waitKey(1) & 0xFF == ord('q')):
            break

    cap.release()
    cv2.destroyAllWindows()


try:
    while True:
        # LED rouge allumÃ©e, verte Ã©teinte
        GPIO.output(18, GPIO.HIGH)
        GPIO.output(23, GPIO.LOW)
        detect()  # Appeler la fonction detect() lorsque la LED rouge est allumÃ©e
        # Rouge reste allumÃ© pendant 2 secondes

        # LED rouge Ã©teinte, verte allumÃ©e
        GPIO.output(18, GPIO.LOW)
        GPIO.output(23, GPIO.HIGH)
        time.sleep(8)  # Vert reste allumÃ© pendant 2 secondes

except KeyboardInterrupt:
    # Nettoyer les configurations GPIO
    GPIO.cleanup()
