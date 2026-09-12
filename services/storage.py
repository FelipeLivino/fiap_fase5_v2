"""Estado local e orçamento de chamadas, persistentes no volume Docker.

SQLite serve apenas à infraestrutura do protótipo. Não substitui a seleção
dos dois bancos da atividade AIRPA.
"""
import json
import sqlite3
import time
from contextlib import contextmanager
from services.errors import ServiceError


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'cardioia.sqlite3'
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY, wa_id TEXT NOT NULL, updated REAL NOT NULL,
                    summary TEXT, pending TEXT
                );
                CREATE TABLE IF NOT EXISTS calls (at REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS calls_at ON calls(at);
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY, result TEXT NOT NULL, created REAL NOT NULL
                );
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            db.row_factory = sqlite3.Row
            # O bloco confirma a transação ao terminar ou desfaz as alterações se houver erro.
            with db:
                yield db
        finally:
            db.close()

    def get(self, token):
        with self.connection() as db:
            row = db.execute('SELECT * FROM conversations WHERE id=?', (token,)).fetchone()
        return dict(row) if row else None

    def create(self, token, wa_id):
        with self.connection() as db:
            db.execute('DELETE FROM conversations WHERE updated<?', (time.time()-86400,))
            db.execute('INSERT OR REPLACE INTO conversations VALUES (?,?,?,NULL,NULL)',
                       (token, wa_id, time.time()))

    def update(self, token, field, value):
        if field not in {'summary', 'pending'}:
            raise ValueError('Campo não permitido')
        with self.connection() as db:
            db.execute(f'UPDATE conversations SET {field}=?, updated=? WHERE id=?',
                       (json.dumps(value, ensure_ascii=False) if value is not None else None,
                        time.time(), token))

    def delete(self, token):
        with self.connection() as db:
            db.execute('DELETE FROM conversations WHERE id=?', (token,))

    def reserve_call(self, limit, interval):
        now = time.time()
        with self.connection() as db:
            # Reservar a escrita antes da contagem impede que processos simultâneos ultrapassem a cota.
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM calls WHERE at<=?', (now-86400,))
            count, last = db.execute('SELECT count(*), max(at) FROM calls').fetchone()
            if count >= limit:
                raise ServiceError('LOCAL_QUOTA', 'Limite local de chamadas em 24 horas atingido.', 429)
            if last and now-last < interval:
                raise ServiceError('LOCAL_RATE_LIMIT', 'Aguarde alguns segundos antes de extrair novamente.', 429)
            db.execute('INSERT INTO calls VALUES (?)', (now,))

    def usage(self):
        with self.connection() as db:
            return db.execute('SELECT count(*) FROM calls WHERE at>?', (time.time()-86400,)).fetchone()[0]

    def cached(self, key):
        with self.connection() as db:
            row = db.execute('SELECT result FROM cache WHERE key=? AND created>?',
                             (key, time.time()-86400)).fetchone()
        return json.loads(row[0]) if row else None

    def save_cache(self, key, value):
        with self.connection() as db:
            db.execute('DELETE FROM cache WHERE created<=?', (time.time()-86400,))
            db.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)',
                       (key, json.dumps(value, ensure_ascii=False), time.time()))
