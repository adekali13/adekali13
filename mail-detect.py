import sqlite3
import http.client
import json
from datetime import datetime

# Étape 1: Créer ou mettre à jour la base de données avec les plaques et les e-mails
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
            # Formatage de la date et de l'heure actuelles
            date_heure_actuelle = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Préparation du message
            message = (f"Nous vous informons que vous avez été en infraction au code de la route le {date_heure_actuelle},"
                       f" en traversant un feu de circulation pour votre plaque {plaque3} . L'amende pour cette violation est de 3000 DA.")

            # Envoi du SMS
            envoyer_sms(numero_destinataire, message)

            print(f"Alerte envoyée à {numero_destinataire} pour la plaque {plaque}.")

            # Marquer que le SMS a été envoyé pour cette plaque
            c.execute("UPDATE utilisateurs SET email_envoye = 1 WHERE plaque = ?", (plaque,))
            conn.commit()

            # Réinitialiser l'indicateur d'envoi pour toutes les autres plaques
            c.execute("UPDATE utilisateurs SET email_envoye = 0 WHERE plaque != ?", (plaque,))
            conn.commit()
        else:
            print("Déjà envoyé")
    else:
        print("Plaque non trouvée dans la base de données.")

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

# pour afficher la base de données
# Connexion à la base de données
conn = sqlite3.connect('plaque_email.db')
c = conn.cursor()
c.execute("SELECT * FROM utilisateurs")
rows = c.fetchall()
print("Plaque | Email")
print("---------------------")
for row in rows:
    print(f"{row[0]} | {row[1]}")
# Fermeture de la connexion à la base de données
conn.close()

plaque3="08381148"
if __name__ == "__main__":
    creer_ou_maj_db()  # Crée la base de données et insère les

    # Exemple de vérification et envoi de SMS pour une plaque détectée
    plaque_detectee = plaque3  # Exemple de plaque détectée
    verifier_plaque_et_envoyer_sms(plaque_detectee)
#suprimer la base de donnes :
