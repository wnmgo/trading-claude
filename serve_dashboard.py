#!/usr/bin/env python3
"""Simple HTTP server to view the dashboard."""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 9110

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Expires', '0')
        super().end_headers()

def main():
    """Start the HTTP server."""
    os.chdir(Path(__file__).parent)
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Dashboard server starting at http://localhost:{PORT}")
        print(f"📊 Open dashboard.html in your browser")
        print(f"📁 To load a transaction log, drag & drop the JSON file or use the file picker")
        print(f"\nPress Ctrl+C to stop the server\n")
        
        # Try to open browser
        try:
            webbrowser.open(f"http://localhost:{PORT}/dashboard.html")
        except:
            pass
        
        httpd.serve_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
