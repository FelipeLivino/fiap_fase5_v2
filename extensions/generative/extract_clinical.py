"""Executar: python -m extensions.generative.extract_clinical --text 'relato fictício'."""
import argparse
import json
from config import settings
from services.storage import Store
from services.gemini_service import GeminiService
from services.errors import ServiceError


def main():
    parser = argparse.ArgumentParser(description='Extrair dados fictícios com Gemini')
    parser.add_argument('--text', required=True)
    args = parser.parse_args()
    if not 1 <= len(args.text.strip()) <= 6000:
        parser.error('O texto deve conter entre 1 e 6000 caracteres.')
    config = settings()
    try:
        result = GeminiService(config, Store(config['DATA_DIR'])).extract(args.text.strip())
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except ServiceError as exc:
        parser.exit(1, f'{exc.code}: {exc.message}\n')


if __name__ == '__main__':
    main()
