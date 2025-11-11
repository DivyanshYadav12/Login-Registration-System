from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import json
import sys
from config import Config
from utils import is_valid_email, get_current_time, validate_password_strength
import database as db

class APIHandler(BaseHTTPRequestHandler):
    
    def _get_post_data(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return {}
            
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                return json.loads(post_data)
            except json.JSONDecodeError:
                parsed_data = parse_qs(post_data)
                # Convert lists to single values
                return {key: value[0] for key, value in parsed_data.items()}
        except Exception as e:
            print(f"Error reading POST data: {e}")
            return {}
    
    def _send_response(self, status_code, data):
        """Send JSON response"""
        response_data = json.dumps(data).encode('utf-8') 
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_data)))
        self.end_headers()
        self.write(response_data)
        
        # Print data
        print(f"[{get_current_time()}] {self.command} {self.path} -> {status_code}")
    
    def do_POST(self):
        """Handle POST requests"""
        data = self._get_post_data()
        
        # Log request (hiding password)
        log_data = data.copy()
        if 'password' in log_data:
            log_data['password'] = '***'
        print(f"[{get_current_time()}] {self.client_address[0]} {self.command} {self.path} - {log_data}")
        
        if self.path == '/register':
            self._handle_register(data)
        elif self.path == '/login':
            self._handle_login(data)
        else:
            self._send_response(404, {"error": "Endpoint not found"})
    
    def _handle_register(self, data):
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        age = data.get('age')
        dob = data.get('dob')
        
        # Validate required fields for registration
        if not name or not email or not password:
            self._send_response(400, {"error": "Name, email and password are required"})
            return
        
        # Validate email format for registration
        if not is_valid_email(email):
            self._send_response(400, {"error": "Invalid email format"})
            return
        
        # Validate password strength
        is_strong, password_error = validate_password_strength(password)
        if not is_strong:
            self._send_response(400, {"error": password_error})
            return
        
        # Register user in database
        result = db.register_user(name, email, password, age, dob)
        
        if 'error' in result:
            error_msg = result['error']
            print(f"Registration error: {error_msg}")
            
            if 'already registered' in error_msg.lower():
                self._send_response(409, {"error": "Email already registered"})
            elif 'database' in error_msg.lower():
                self._send_response(500, {"error": error_msg})
            else:
                self._send_response(500, {"error": error_msg})
        else:
            self._send_response(201, {
                "message": "User registered successfully",
                "user_id": result["user_id"],
                "name": result["name"],
                "email": result["email"]
            })
    
    def _handle_login(self, data):
        email = data.get('email', '').strip()
        user_id = data.get('user_id', '').strip()
        password = data.get('password', '')
        
        # Validate required fields for login
        if not password:
            self._send_response(400, {"error": "Password is required"})
            return
        
        # Checking if both email and user_id are provided 
        if email and user_id:
            self._send_response(400, {"error": "Provide either email or user_id, not both"})
            return
        
        # Checking if neither email nor user_id is provided
        if not email and not user_id:
            self._send_response(400, {"error": "Email or user_id is required"})
            return
        
        # Validateing email format if email is provided
        if email and not is_valid_email(email):
            self._send_response(400, {"error": "Invalid email format"})
            return
        
        # Login user - pass both email and user_id to the database function
        result = db.login_user(email=email, password=password, user_id=user_id)
        
        if 'error' in result:
            error_msg = result['error']
            print(f"Login error: {error_msg}")
            
            if 'not found' in error_msg.lower():
                self._send_response(404, {"error": "User not found"})
            elif 'invalid password' in error_msg.lower():
                self._send_response(401, {"error": "Invalid password"})
            elif 'database' in error_msg.lower():
                self._send_response(500, {"error": error_msg})
            else:
                self._send_response(500, {"error": error_msg})
        else:
            self._send_response(200, {
                "message": "Login successful",
                "user_id": result["user_id"],
                "name": result["name"],
                "email": result["email"]
            })

def run_server():
    if not db.init_db():
        print("Failed to initialize database. Exiting.")
        return
    
    # Create and start server
    server = HTTPServer((Config.SERVER_HOST, Config.SERVER_PORT), APIHandler)
    print(f"Server running on http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
    print("Endpoints:")
    print("  POST /register - Register new user")
    print("  POST /login    - Login user (with email or user_id)")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()

if __name__ == '__main__':
    run_server()