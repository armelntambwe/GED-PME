"""Envoi d'alertes WhatsApp (Twilio, Meta Cloud API ou CallMeBot)."""
import json
import logging
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import base64

from config import (
    APP_BASE_URL,
    CALLMEBOT_API_KEY,
    DEFAULT_PHONE_PREFIX,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_FROM,
    WHATSAPP_ENABLED,
    WHATSAPP_IMPORTANT_TYPES,
    WHATSAPP_META_PHONE_ID,
    WHATSAPP_META_TOKEN,
    WHATSAPP_PROVIDER,
)

logger = logging.getLogger(__name__)

IMPORTANT_TYPES = set(WHATSAPP_IMPORTANT_TYPES)

_NETWORK_RETRY_DELAY = 2


def _friendly_network_error(exc):
    """Message clair pour les erreurs réseau courantes (Windows, DNS, proxy…)."""
    msg = str(exc).lower()
    reason = getattr(exc, 'reason', None)
    if reason is not None:
        msg = f'{msg} {reason}'.lower()

    if any(x in msg for x in ('getaddrinfo failed', '11001', '11002', 'name or service not known', 'nodename nor servname')):
        return (
            "Connexion impossible à l'API CallMeBot (api.callmebot.com). "
            "Le serveur Flask n'a pas accès à Internet ou le DNS ne répond pas. "
            "Vérifiez : connexion Wi‑Fi/4G, pare-feu Windows (autoriser Python), "
            "DNS (essayez 8.8.8.8), puis testez https://api.callmebot.com dans le navigateur."
        )
    if 'timed out' in msg or 'timeout' in msg:
        return "Délai dépassé en contactant CallMeBot — connexion lente ou bloquée. Réessayez."
    if 'connection refused' in msg or '10061' in msg:
        return "Connexion refusée par CallMeBot — réessayez dans quelques minutes."
    if 'certificate' in msg or 'ssl' in msg or 'tls' in msg:
        return "Erreur SSL vers CallMeBot — vérifiez la date/heure de votre PC."
    if 'proxy' in msg:
        return (
            "Erreur proxy réseau. Si vous êtes derrière un proxy, "
            "définissez HTTPS_PROXY dans le fichier .env du serveur."
        )
    return str(exc)


def _urlopen_with_retry(req, timeout=20, retries=2):
    """Ouvre une URL avec prise en charge proxy et nouvelle tentative sur erreur réseau."""
    proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    if proxy:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
        )
    else:
        opener = urllib.request.build_opener()

    last_err = None
    for attempt in range(retries):
        try:
            return opener.open(req, timeout=timeout)
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(_NETWORK_RETRY_DELAY)
                continue
            raise last_err from e
    raise last_err


def is_important_notification(type_notif):
    return (type_notif or '') in IMPORTANT_TYPES


def is_whatsapp_configured():
    if not WHATSAPP_ENABLED:
        return False
    provider = (WHATSAPP_PROVIDER or '').lower()
    if provider == 'twilio':
        return bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_FROM)
    if provider == 'meta':
        return bool(WHATSAPP_META_TOKEN and WHATSAPP_META_PHONE_ID)
    if provider == 'callmebot':
        return True
    return False


def normalize_phone(telephone):
    """Convertit un numéro local en format international (+243…)."""
    if not telephone:
        return None
    raw = re.sub(r'[\s\-\(\)\.]', '', str(telephone).strip())
    if not raw:
        return None
    if raw.startswith('+'):
        digits = '+' + re.sub(r'\D', '', raw[1:])
        return digits if len(digits) > 8 else None
    digits = re.sub(r'\D', '', raw)
    if digits.startswith('00'):
        return '+' + digits[2:]
    prefix = (DEFAULT_PHONE_PREFIX or '+243').lstrip('+')
    if digits.startswith(prefix):
        return '+' + digits
    if digits.startswith('0'):
        return '+' + prefix + digits[1:]
    if len(digits) >= 9:
        return '+' + prefix + digits
    return None


def format_alert_message(message, lien=None):
    text = f"🔔 GED-PME\n{message}"
    if lien:
        url = lien if lien.startswith('http') else f"{APP_BASE_URL.rstrip('/')}{lien}"
        text += f"\n\n👉 {url}"
    return text


def _http_post_json(url, payload, headers=None):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with _urlopen_with_retry(req, timeout=20) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))


def _http_post_form(url, form_data, headers=None):
    data = urllib.parse.urlencode(form_data).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with _urlopen_with_retry(req, timeout=20) as resp:
        body = resp.read().decode('utf-8')
        try:
            return resp.status, json.loads(body)
        except json.JSONDecodeError:
            return resp.status, {'raw': body}


def _http_get(url):
    req = urllib.request.Request(url, method='GET')
    with _urlopen_with_retry(req, timeout=20) as resp:
        return resp.status, resp.read().decode('utf-8')


def _send_twilio(phone, message):
    to = phone if phone.startswith('whatsapp:') else f'whatsapp:{phone}'
    from_num = TWILIO_WHATSAPP_FROM
    if not from_num.startswith('whatsapp:'):
        from_num = f'whatsapp:{from_num}'
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    status, result = _http_post_form(
        url,
        {'From': from_num, 'To': to, 'Body': message},
        headers={'Authorization': f'Basic {auth}'},
    )
    if status in (200, 201):
        return True, 'Message WhatsApp envoyé (Twilio)'
    return False, result.get('message') or str(result)


def _send_meta(phone, message):
    digits = re.sub(r'\D', '', phone)
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_META_PHONE_ID}/messages"
    payload = {
        'messaging_product': 'whatsapp',
        'to': digits,
        'type': 'text',
        'text': {'body': message[:4096]},
    }
    status, result = _http_post_json(
        url,
        payload,
        headers={'Authorization': f'Bearer {WHATSAPP_META_TOKEN}'},
    )
    if status in (200, 201):
        return True, 'Message WhatsApp envoyé (Meta)'
    err = result.get('error', {})
    return False, err.get('message') or str(result)


def _send_callmebot(phone, message, api_key):
    if not api_key:
        return False, 'Clé API CallMeBot manquante — activez CallMeBot et saisissez la clé dans votre profil'
    phone_param = phone if phone.startswith('+') else '+' + re.sub(r'\D', '', phone)
    qs = urllib.parse.urlencode({
        'phone': phone_param,
        'text': message[:1500],
        'apikey': api_key,
    })
    url = f'https://api.callmebot.com/whatsapp.php?{qs}'
    try:
        status, body = _http_get(url)
        body_lower = (body or '').lower()
        if status == 200 and ('message sent' in body_lower or 'added' in body_lower or 'success' in body_lower):
            return True, 'Message WhatsApp envoyé (CallMeBot)'
        if status in (200, 201) and 'error' not in body_lower and len(body.strip()) < 80:
            return True, 'Message WhatsApp envoyé (CallMeBot)'
        return False, (body or 'Erreur CallMeBot').strip()[:500]
    except urllib.error.HTTPError as e:
        return False, e.read().decode('utf-8', errors='replace') or str(e)
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as e:
        return False, _friendly_network_error(e)


def send_alert_to_user(user, message, lien=None):
    """
    Envoie une alerte WhatsApp à un utilisateur si notify_whatsapp est activé.
    Retourne (success: bool, detail: str).
    """
    if not user or not getattr(user, 'notify_whatsapp', False):
        return False, 'WhatsApp désactivé pour cet utilisateur'

    if not WHATSAPP_ENABLED:
        logger.debug('WhatsApp désactivé globalement (WHATSAPP_ENABLED=false)')
        return False, 'WhatsApp non activé sur le serveur'

    phone = normalize_phone(getattr(user, 'telephone', None))
    if not phone:
        return False, 'Numéro de téléphone manquant dans le profil'

    text = format_alert_message(message, lien)
    provider = (WHATSAPP_PROVIDER or 'callmebot').lower()

    try:
        if provider == 'twilio':
            if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_FROM):
                return False, 'Twilio non configuré (variables TWILIO_*)'
            return _send_twilio(phone, text)

        if provider == 'meta':
            if not (WHATSAPP_META_TOKEN and WHATSAPP_META_PHONE_ID):
                return False, 'Meta WhatsApp non configuré (WHATSAPP_META_*)'
            return _send_meta(phone, text)

        if provider == 'callmebot':
            api_key = getattr(user, 'whatsapp_api_key', None) or CALLMEBOT_API_KEY
            return _send_callmebot(phone, text, api_key)

        return False, f'Fournisseur WhatsApp inconnu: {provider}'
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        logger.error('WhatsApp HTTP %s: %s', e.code, body)
        return False, f'Erreur WhatsApp ({e.code})'
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as e:
        logger.error('WhatsApp network error: %s', e)
        return False, _friendly_network_error(e)
    except Exception as e:
        logger.error('WhatsApp send error: %s', e)
        return False, str(e)


def check_callmebot_connectivity(timeout=10):
    """Teste si le serveur peut joindre api.callmebot.com (diagnostic)."""
    try:
        req = urllib.request.Request('https://api.callmebot.com/', method='GET')
        with _urlopen_with_retry(req, timeout=timeout, retries=1) as resp:
            return True, f'API CallMeBot joignable (HTTP {resp.status})'
    except Exception as e:
        return False, _friendly_network_error(e)
def send_test_alert(user):
    return send_alert_to_user(
        user,
        "Ceci est un message test GED-PME. Vos alertes WhatsApp fonctionnent correctement.",
        '/dashboard-employee',
    )
