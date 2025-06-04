import http.server
import socketserver
import os
import urllib.parse
import json
from database import Database
from auth import Auth
import config
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from config import DB_CONFIG


PORT = 8000
db = Database()
auth = Auth()

class RequestHandler(http.server.SimpleHTTPRequestHandler):
       def do_GET(self):

           if self.path == '/':
               self.path = 'templates/index.html'
           
           elif self.path.startswith('static/'):
               self.path = self.path[1:]  
           elif self.path in ['/about', '/abiturient', '/admission', '/location', '/login', '/admin']:
               self.path = f'templates{self.path}.html'
           
           try:
               return super().do_GET()
           except FileNotFoundError:
               self.send_error(404, "Page not found")

def handle_api_get(self):
        if self.path == '/api/news':
            page = int(self.get_param('page', 1))
            per_page = 5
            news = db.get_news(page, per_page)
            self.send_json(news)

def handle_news_post(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        if auth.is_authenticated(self):
            db.add_news(data['title'], data['content'], data.get('image'))
            self.send_json({'status': 'success'})
        else:
            self.send_error(401)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
class RequestHandler(http.server.SimpleHTTPRequestHandler):
       def do_GET(self):
          
           if self.path == '/api/check-auth':
               self.send_response(200)
               self.send_header('Content-type', 'application/json')
               self.end_headers()
               
               
               cookies = self.headers.get('Cookie', '')
               is_authenticated = 'session_id=admin' in cookies  
               
               response = json.dumps({'isAdmin': is_authenticated}).encode()
               self.wfile.write(response)
               return
def do_POST(self):
       if self.path == '/login':
           content_length = int(self.headers['Content-Length'])
           post_data = self.rfile.read(content_length)
           data = json.loads(post_data)

           
           if data['username'] == 'admin' and data['password'] == 'admin123':
               self.send_response(302)
               self.send_header('Location', '/admin')
               self.send_header('Set-Cookie', 'session_id=admin')
               self.end_headers()
           else:
               self.send_error(401, "Invalid credentials")
class RequestHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_POST(self):
        if self.path == '/api/admins':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            
            try:
               
                auth_header = self.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    self.send_error(401)
                    return
                
                token = auth_header.split(' ')[1]
                current_user = auth.validate_token(token)  # Реализуйте метод валидации токена
                
                auth.create_admin(
                    current_user_id=current_user['id'],
                    new_username=post_data['username'],
                    new_password=post_data['password']
                )
                
                self.send_response(201)
                self.end_headers()
                
            except Exception as e:
                self.send_error(400, message=str(e))

def check_admin_auth(handler):
    def wrapper(*args, **kwargs):
        if not handler.headers.get('Authorization'):
            handler.send_error(401)
            return
        
        return handler(*args, **kwargs)
    return wrapper
class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type="text/html"):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        try:
            if self.path == "/":
                self._set_headers()
                with open("templates/index.html", "rb") as f:
                    self.wfile.write(f.read())
            elif self.path == "/login":
                self._set_headers()
                with open("templates/login.html", "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404)
                self.wfile.write(b"404 Not Found")
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(f"Server Error: {str(e)}".encode())

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        
        try:
            if self.path == "/login":
                # Обрабатываем JSON или form-data
                if "application/json" in self.headers.get("Content-Type", ""):
                    data = json.loads(post_data.decode())
                    username = data.get("username")
                    password = data.get("password")
                else:
                    data = parse_qs(post_data.decode())
                    username = data.get("username", [""])[0]
                    password = data.get("password", [""])[0]

                auth = Auth()
                user = auth.authenticate(username, password)
                
                if user and user.get("is_admin"):
                    response = {"status": "success", "redirect": "/admin"}
                    self._set_headers(200, "application/json")
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self._set_headers(401)
                    self.wfile.write(b"Authentication failed")
            
            else:
                self._set_headers(501)
                self.wfile.write(b"Unsupported method")
                
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(f"Error: {str(e)}".encode())

def run_server():
    server = HTTPServer(("0.0.0.0", 8000), RequestHandler)
    print("Server running at http://localhost:8000")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
    class RequestHandler(BaseHTTPRequestHandler):
        def _send_response(self, content, status=200, content_type="text/html"):
         self.send_response(status)
         self.send_header("Content-type", content_type)
         self.end_headers()
         self.wfile.write(content.encode() if isinstance(content, str) else content)

    def do_GET(self):
        try:
            if self.path == "/":
                with open("templates/index.html", "rb") as f:
                    self._send_response(f.read())
            elif self.path == "/login":
                with open("templates/login.html", "rb") as f:
                    self._send_response(f.read())
            else:
                self._send_response("404 Not Found", 404)
        except FileNotFoundError:
            self._send_response("404 Not Found", 404)
        except Exception as e:
            self._send_response(f"Server Error: {str(e)}", 500)

    def do_POST(self):
        try:
            if self.path == "/login":
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)
                data = parse_qs(post_data.decode())

                auth = Auth()
                user = auth.authenticate(
                    data.get("username", [""])[0],
                    data.get("password", [""])[0]
                )

                if user and user.get("is_admin"):
                    self._send_response("", 302, headers={"Location": "/admin"})
                else:
                    self._send_response("Invalid credentials", 401)
            else:
                self._send_response("Method Not Allowed", 405)
        except Exception as e:
            self._send_response(f"Error: {str(e)}", 500)

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
    class RequestHandler(BaseHTTPRequestHandler):
     def do_GET(self):
        try:
            if self.path == "/":
                with open("templates/index.html", "rb") as f:
                    self._send_response(f.read())
            elif self.path == "/login":
                with open("templates/login.html", "rb") as f:
                    self._send_response(f.read())
            elif self.path == "/favicon.ico":
                self._send_response(b"", 204)  # No Content
            else:
                self._send_response("404 Not Found", 404)
        except FileNotFoundError:
            self._send_response("404 Not Found", 404)
        except Exception as e:
            self._send_response(f"Server Error: {str(e)}", 500)
            class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/favicon.ico":
            # Возвращаем статус 204 (No Content)
            self.send_response(204)
            self.end_headers()
            return
        
        # Остальная логика обработки GET-запросов
        if self.path == "/":
            self.send_response(200)