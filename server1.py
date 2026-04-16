"""
server.py -- drop this in your Portfolio folder and run:
    python server.py

Serves on http://localhost:8000 with proper Range request support.
This is what Python's built-in http.server is missing -- video needs it.
"""

import http.server
import os
import sys

class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        f = None

        if os.path.isdir(path):
            return super().send_head()

        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        ctype = self.guess_type(path)
        fs = os.fstat(f.fileno())
        file_size = fs[6]

        range_header = self.headers.get('Range')

        if range_header:
            # Parse "bytes=start-end"
            try:
                ranges = range_header.strip().replace('bytes=', '')
                start_str, end_str = ranges.split('-')
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206, 'Partial Content')
                self.send_header('Content-type', ctype)
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Content-Length', str(length))
                self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
                self.end_headers()
                f.seek(start)
                self.copyfile_range(f, self.wfile, length)
                f.close()
                return None
            except Exception as e:
                print(f'Range error: {e}')
                f.seek(0)

        # Normal (non-range) response
        self.send_response(200)
        self.send_header('Content-type', ctype)
        self.send_header('Content-Length', str(file_size))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def copyfile_range(self, source, outputfile, length):
        bufsize = 64 * 1024
        remaining = length
        while remaining > 0:
            chunk = min(bufsize, remaining)
            data = source.read(chunk)
            if not data:
                break
            outputfile.write(data)
            remaining -= len(data)

    def log_message(self, format, *args):
        # Quieter logging -- only show non-200/206
        code = args[1] if len(args) > 1 else ''
        if code not in ('200', '206', '304'):
            super().log_message(format, *args)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = http.server.HTTPServer(('', port), RangeHTTPRequestHandler)
    print(f'Serving on http://localhost:{port}')
    print('Range requests supported -- videos will load correctly.')
    print('Ctrl+C to stop.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
