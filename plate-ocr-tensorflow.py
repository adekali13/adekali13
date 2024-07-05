import cv2
import numpy as np
from tensorflow.lite.python.interpreter import Interpreter
import pytesseract
from PIL import Image
from collections import Counter

# Configuration initiale
modelpath = 'detect.tflite'
lblpath = 'labelmap.txt'
min_conf = 0.5

#cap = cv2.VideoCapture(1)
cap = cv2.VideoCapture('demo.mp4')
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

# Configuration de Pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Stocker les lectures de plaques pour analyse
lectures_plaques = []

while True:
    ret, frame = cap.read()
    if not ret:
        break

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (width, height))
    input_data = np.expand_dims(image_resized, axis=0)

    if float_input:
        input_data = (np.float32(input_data) - input_mean) / input_std

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    boxes = interpreter.get_tensor(output_details[1]['index'])[0]
    classes = interpreter.get_tensor(output_details[3]['index'])[0]
    scores = interpreter.get_tensor(output_details[0]['index'])[0]

    for i in range(len(scores)):
        if (scores[i] > min_conf) and (scores[i] <= 1.0):
            ymin, xmin, ymax, xmax = [int(max(1, box * dim)) for box, dim in
                                      zip(boxes[i], [frame.shape[0], frame.shape[1], frame.shape[0], frame.shape[1]])]

            plaque_image = frame[ymin:ymax, xmin:xmax]
            plaque_image_pil = Image.fromarray(plaque_image)
            texte_plaque = pytesseract.image_to_string(plaque_image_pil, lang='fra').strip()

            if texte_plaque:
                lectures_plaques.append(texte_plaque)

                # Analyser les lectures tous les 10 captures
                if len(lectures_plaques) == 5:
                    lecture_frequente = Counter(lectures_plaques).most_common(1)[0]
                    print(f"Lecture la plus fréquente : {lecture_frequente[0]} ({lecture_frequente[1]}/5 fois)")
                    lectures_plaques = []  # Réinitialiser pour le prochain ensemble de lectures

    cv2.imshow('output', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
