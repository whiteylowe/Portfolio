"""
server.py -- run this from your Portfolio folder:
    python server.py

Handles Range requests so videos load properly in the browser.
"""

import http.server
import os
import sys

class RangeHandler(http.server.SimpleHTTPRequestHandler):

    def send_head(self):
        path = self.translate_path(self.path)

        if os.path.isdir(path):
            return super().send_head()

        if not os.path.isfile(path):
            self.send_error(404, "File not found")
            return None

        ctype = self.guess_type(path)
        file_size = os.path.getsize(path)
        range_header = self.headers.get('Range')

        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(403)
            return None

        if range_header:
            try:
                byte_range = range_header.strip().replace('bytes=', '')
                start_str, end_str = byte_range.split('-')
                start = int(start_str) if start_str.strip() else 0
                end = int(end_str) if end_str.strip() else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                f.seek(start)
                self.send_response(206)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(length))
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                self._send_bytes(f, length)
                f.close()
                return None
            except Exception:
                f.seek(0)

        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(file_size))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        return f

    def _send_bytes(self, f, length):
        remaining = length
        while remaining > 0:
            chunk = f.read(min(65536, remaining))
            if not chunk:
                break
            try:
                self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
            remaining -= len(chunk)

    def log_message(self, fmt, *args):
        code = str(args[1]) if len(args) > 1 else ''
        if not code.startswith('2') and not code.startswith('3'):
            super().log_message(fmt, *args)


class QuietServer(http.server.HTTPServer):
    def handle_error(self, request, client_address):
        pass


if __name__ == '__main__':
    port = 8000
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = QuietServer(('', port), RangeHandler)
    print(f'Server running at http://localhost:{port}')
    print('Videos will now load correctly.')
    print('Press Ctrl+C to stop.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
