"""Internationalisation légère FR / EN."""
from flask import request, session

SUPPORTED = ('fr', 'en')
DEFAULT_LANG = 'fr'
COOKIE_NAME = 'ged_lang'


def get_lang():
    lang = session.get('lang') or request.cookies.get(COOKIE_NAME)
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    return lang


def set_language(response, lang):
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    session['lang'] = lang
    response.set_cookie(COOKIE_NAME, lang, max_age=31536000, samesite='Lax')
    return response


def translate(key, lang=None, **kwargs):
    from translations.messages import MESSAGES
    lang = lang or get_lang()
    bucket = MESSAGES.get(lang) or MESSAGES[DEFAULT_LANG]
    text = bucket.get(key) or MESSAGES[DEFAULT_LANG].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def workflow_step_texts(lang=None):
    lang = lang or get_lang()
    return [translate(f'home.workflow.detail.{i}', lang) for i in range(7)]
