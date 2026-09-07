"""Configuração injetada pelo Docker Compose; nenhum segredo em código."""
import os
from pathlib import Path


def settings():
    return {
        'SECRET_KEY': os.getenv('FLASK_SECRET_KEY', ''),
        'DATA_DIR': Path(os.getenv('APP_DATA_DIR', 'runtime')),
        'WA_API_KEY': os.getenv('WA_API_KEY', ''),
        'WA_URL': os.getenv('WA_URL', ''),
        'WA_ASSISTANT_ID': os.getenv('WA_ASSISTANT_ID', ''),
        'WA_ENVIRONMENT_ID': os.getenv('WA_ENVIRONMENT_ID', ''),
        'WA_API_VERSION': os.getenv('WA_API_VERSION', '2024-08-25'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
        'GEMINI_MODEL': os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite'),
        'GEMINI_DAILY_LIMIT': min(500, max(1, int(os.getenv('GEMINI_DAILY_LIMIT', '500')))),
        'GEMINI_MIN_INTERVAL_SECONDS': max(0, int(os.getenv('GEMINI_MIN_INTERVAL_SECONDS', '10'))),
        'MAX_CONTENT_LENGTH': 32768,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Strict',
    }
