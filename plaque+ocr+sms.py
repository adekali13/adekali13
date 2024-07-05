import cv2
import numpy as np
from tensorflow.lite.python.interpreter import Interpreter
import pytesseract
from PIL import Image
from collections import Counter
import re  # Ajouté pour utiliser les expressions régulières
import sqlite3
import http.client
import json
from datetime import datetime

# Configuration initiale
modelpath = 'detect.tflite'
lblpath = 'labelmap.txt'
min_conf = 0.5

# Initialisation de la capture vidéo
cap = cv2.VideoCapture(0)  # Utiliser 0 pour une webcam
interpreter = Interpreter(model_path=modelpath)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]
float_input = (input_details[0]['dtype'] == np.float32)
input_mean = 127.5
input_std = 127.5

# Lecture des labels
with open(lblpath, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

# Configuration de Pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# Fonction pour filtrer les caractères non désirés
def filtrer_texte(texte):
    pattern = re.compile('[^A-Z0-9]+')
    texte_filtré = pattern.sub('', texte)
    return texte_filtré


# Stocker les lectures de plaques pour analyse
lectures_plaques = []
plaque3 = ""

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Prétraitement de l'image
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

    # Traitement des résultats de la détection
    for i in range(len(scores)):
        if (scores[i] > min_conf) and (scores[i] <= 1.0):
            ymin, xmin, ymax, xmax = [int(max(1, box * dim)) for box, dim in
                                      zip(boxes[i], [frame.shape[0], frame.shape[1], frame.shape[0], frame.shape[1]])]

            plaque_image = frame[ymin:ymax, xmin:xmax]
            plaque_image_pil = Image.fromarray(plaque_image)
            texte_plaque = pytesseract.image_to_string(plaque_image_pil, lang='fra').strip()

            # Appliquer le filtrage sur le texte détecté
            texte_plaque_filtré = filtrer_texte(texte_plaque)

            if texte_plaque_filtré:
                lectures_plaques.append(texte_plaque_filtré)

                # Analyser les lectures tous les 5 captures
                if len(lectures_plaques) % 4 == 0:
                    lecture_frequente = Counter(lectures_plaques).most_common(1)[0]
                    print(f"Lecture la plus fréquente : {lecture_frequente[0]} ({lecture_frequente[1]}/4 fois)")
                    lectures_plaques = []  # Réinitialiser pour le prochain ensemble de lectures
                    plaque3 = lecture_frequente[0]
                    print(plaque3)


    def creer_ou_maj_db():
        conn = sqlite3.connect('plaque_email.db')
        c = conn.cursor()

        # Création de la table s'il n'en existe pas déjà une, avec une colonne supplémentaire pour suivre si un email a été envoyé
        c.execute('''CREATE TABLE IF NOT EXISTS utilisateurs
                     (plaque TEXT PRIMARY KEY, email TEXT, email_envoye INTEGER DEFAULT 0)''')

        # Insertion des plaques et e-mails, avec la colonne 'email_envoye' initialisée à 0 par défaut
        plaques_emails = [
            ('255911631', '213790074707'),
            ('08381148', '213658357356'),

        ]

        # Utilisation de INSERT OR IGNORE pour éviter les erreurs en cas de doublons
        c.executemany("INSERT OR IGNORE INTO utilisateurs (plaque, email) VALUES (?, ?)", plaques_emails)

        conn.commit()
        conn.close()


    # Assurez-vous d'appeler cette fonction avant d'utiliser la table `utilisateurs` dans votre script

    # Étape 2: Vérification des plaques et envoi de SMS
    def verifier_plaque_et_envoyer_sms(plaque):
        conn = sqlite3.connect('plaque_email.db')
        c = conn.cursor()
        # Vérification de l'existence de la plaque dans la base de données et si un SMS a déjà été envoyé
        c.execute("SELECT email, email_envoye FROM utilisateurs WHERE plaque = ?", (plaque,))
        result = c.fetchone()

        if result:
            numero_destinataire, sms_envoye = result
            if not sms_envoye:

                date_heure_actuelle = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                message = (
                    f"Nous vous informons que vous avez été en infraction au code de la route le {date_heure_actuelle},"
                    f" en traversant un feu de circulation pour votre plaque {plaque3} . "
                    f"L'amende pour cette violation est de 3000 DA.")
                envoyer_sms(numero_destinataire, message)

                print(f"Alerte envoyée à {numero_destinataire} pour la plaque {plaque}.")

                c.execute("UPDATE utilisateurs SET email_envoye = 1 WHERE plaque = ?", (plaque,))
                conn.commit()
                c.execute("UPDATE utilisateurs SET email_envoye = 0 WHERE plaque != ?", (plaque,))
                conn.commit()
            else:
                print("Déjà envoyé")
        else:
            print(" ")

        conn.close()


    def envoyer_sms(numero, message):
        conn = http.client.HTTPSConnection("1vdmlx.api.infobip.com")
        payload = json.dumps({
            "messages": [
                {
                    "destinations": [{"to": numero}],
                    "from": "ServiceSMS",
                    "text": message
                }
            ]
        })
        headers = {
            'Authorization': 'App c4fea0ef887a51f1d42c512785a90192-6c9cf915-1a47-4a13-968f-cd2b74ab7e63',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        conn.request("POST", "/sms/2/text/advanced", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))

    if __name__ == "__main__":
        creer_ou_maj_db()  # Crée la base de données et insère les

        # Exemple de vérification et envoi de SMS pour une plaque détectée
        plaque_detectee = plaque3  # Exemple de plaque détectée
        verifier_plaque_et_envoyer_sms(plaque_detectee)
    # Affichage de l'image
    cv2.imshow('output', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
