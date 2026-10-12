#!/usr/bin/env python3
"""Локальный сервер для планшета: раздаёт страницу и обновляет news.json раз в 10 минут.
Запуск: python server.py  -> откройте на iPad адрес, который будет напечатан."""
import functools
import socket
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import fetch_news

PORT = 8080
REFRESH_SECONDS = 600
ROOT = Path(__file__).parent


def refresher():
    while True:
        try:
            n, errs = fetch_news.build()
            print(f"[{time.strftime('%H:%M:%S')}] новостей: {n}", *errs, sep="\n  " if errs else " ")
        except Exception as e:
            print("Ошибка обновления:", e)
        time.sleep(REFRESH_SECONDS)


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "localhost"
    finally:
        s.close()


class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    threading.Thread(target=refresher, daemon=True).start()
    handler = functools.partial(NoCache, directory=str(ROOT))
    print(f"Откройте на iPad: http://{lan_ip()}:{PORT}/")
    ThreadingHTTPServer(("0.0.0.0", PORT), handler).serve_forever()
