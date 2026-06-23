import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import MAIL_ENABLED, MAIL_FROM, MAIL_PASSWORD, MAIL_PORT, MAIL_SERVER, MAIL_USERNAME


def send_document_email(destinataire, sujet, message, filepath, filename):
    """Envoie un document en pièce jointe si SMTP configuré."""
    if not MAIL_ENABLED or not MAIL_USERNAME or not MAIL_PASSWORD:
        return False, 'Envoi SMTP non configuré sur le serveur'

    if not os.path.isfile(filepath):
        return False, 'Fichier introuvable'

    msg = MIMEMultipart()
    msg['From'] = MAIL_FROM
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.attach(MIMEText(message, 'plain', 'utf-8'))

    with open(filepath, 'rb') as f:
        part = MIMEApplication(f.read(), Name=filename)
    part['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(part)

    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)

    return True, 'Document envoyé par email'
