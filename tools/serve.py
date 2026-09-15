#!/usr/bin/env python3
"""Local preview only. Production still uses the tested Apache .htaccess rules."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
import argparse

ROOT = Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parts = urlsplit(self.path)
        path = unquote(parts.path)
        if path.split('/')[1] in ('src', 'tools', 'tests', 'docs', '.git'):
            self.send_error(403); return
        candidate = (ROOT / path.lstrip('/')).resolve()
        if candidate != ROOT and ROOT not in candidate.parents:
            self.send_error(403); return
        if candidate.suffix == '' and candidate.with_suffix('.html').is_file():
            self.path = parts.path + '.html' + ('?' + parts.query if parts.query else '')
        super().do_GET()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, default=8765)
    args = ap.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT)))
    print(f'Preview: http://127.0.0.1:{args.port}', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
if __name__ == '__main__': main()
