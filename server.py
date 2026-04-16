import http.server, os, sys

class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        if not os.path.isfile(path):
            self.send_error(404)
            return None
        size = os.path.getsize(path)
        ctype = self.guess_type(path)
        rng = self.headers.get('Range', '')
        f = open(path, 'rb')
        if rng.startswith('bytes='):
            try:
                r = rng[6:].split('-')
                s = int(r[0]) if r[0] else 0
                e = int(r[1]) if r[1] else size - 1
                e = min(e, size - 1)
                f.seek(s)
                self.send_response(206)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Range', 'bytes %d-%d/%d' % (s, e, size))
                self.send_header('Content-Length', str(e - s + 1))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                left = e - s + 1
                while left:
                    d = f.read(min(65536, left))
                    if not d: break
                    try: self.wfile.write(d)
                    except: break
                    left -= len(d)
                f.close()
                return None
            except: f.seek(0)
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(size))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        return f

    def log_message(self, fmt, *args): pass

class Server(http.server.HTTPServer):
    def handle_error(self, req, addr): pass

os.chdir(os.path.dirname(os.path.abspath(__file__)))
s = Server(('', 8000), Handler)
print('http://localhost:8000  (Ctrl+C to stop)')
try: s.serve_forever()
except KeyboardInterrupt: print('Stopped.')
