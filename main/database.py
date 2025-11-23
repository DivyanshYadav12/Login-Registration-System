import mysql.connector
from mysql.connector import Error
import uuid
from datetime import datetime, timedelta
from config import Config
from utils import hash_password, verify_password, generate_user_id, normalize_email
from utils import generate_reset_token, validate_password_strength

def create_connection():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            auth_plugin='mysql_native_password'
        )
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def initialize_db():
    conn = create_connection()
    if not conn:
        print("Failed to connect to database")
        return False
        
    try:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                age INT,
                dob DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create password_reset_tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                token VARCHAR(100) UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        print("Database tables created successfully")
        return True
    except Error as e:
        print(f"Database initialization error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def register_user(name, email, password, age=None, dob=None):
    print(f"Attempting to register user: {email}")
    
    conn = create_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Normalize email
        email = normalize_email(email)
        print(f"Normalized email: {email}")
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"Email already exists: {email}")
            return {"error": "Email already registered"}
        
        # Generate user data
        user_id = generate_user_id()
        hashed_password = hash_password(password)
        print(f"Generated user ID: {user_id}")
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (id, name, email, password_hash, age, dob)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, name, email, hashed_password, age, dob))
        
        conn.commit()
        print(f"User registered successfully: {user_id}")
        
        return {
            "message": "Registration successful",
            "user_id": user_id,
            "name": name,
            "email": email
        }
        
    except Error as e:
        print(f"Database error during registration: {e}")
        return {"error": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

def login_user(email=None, password=None, user_id=None):
    """Login user via email or user_id and password"""
    print(f"Attempting login - Email: {email}, User ID: {user_id}")
    
    conn = create_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        cursor = conn.cursor(dictionary=True)

        if user_id:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
        else:
            email = normalize_email(email)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
        
        if not user:
            return {"error": "User not found"}
        
        print(f"User found: {user['id']} - {user['name']}")
        
        if verify_password(user["password_hash"], password):
            print("Password verified successfully")
            return {
                "user_id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        else:
            print("Invalid password")
            return {"error": "Invalid password"}
            
    except Error as e:
        print(f"Database error during login: {e}")
        return {"error": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

def forgot_password(email):
    """Generate reset token for user"""
    print(f"🔐 Forgot password request for: {email}")
    
    conn = create_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists
        email = normalize_email(email)
        cursor.execute("SELECT id, name, email FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            return {"error": "User not found"}
        
        # Generate reset token
        reset_token = generate_reset_token()
        expires_at = datetime.now() + timedelta(hours=1)  # 1 hour expiry
        
        # Store token in database
        cursor.execute("""
            INSERT INTO password_reset_tokens (id, user_id, token, expires_at)
            VALUES (%s, %s, %s, %s)
        """, (str(uuid.uuid4()), user['id'], reset_token, expires_at))
        
        conn.commit()
        
        print(f"Reset token generated for: {email}")
        
        return {
            "success": True,
            "message": "Reset token generated",
            "reset_token": reset_token,
            "user_id": user['id'],
            "email": user['email']
        }
        
    except Error as e:
        print(f"Database error: {e}")
        return {"error": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

def reset_password(token, new_password):
    """Reset password using valid token"""
    print(f"Resetting password with token...")
    
    conn = create_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check if token is valid and not expired
        cursor.execute("""
            SELECT prt.*, u.id as user_id 
            FROM password_reset_tokens prt 
            JOIN users u ON prt.user_id = u.id 
            WHERE prt.token = %s AND prt.expires_at > NOW()
        """, (token,))
        
        token_data = cursor.fetchone()
        
        if not token_data:
            return {"error": "Invalid or expired reset token"}
        
        # Validate new password
        is_strong, password_error = validate_password_strength(new_password)
        if not is_strong:
            return {"error": password_error}
        
        # Hash new password
        hashed_password = hash_password(new_password)
        
        # Update user password
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", 
                      (hashed_password, token_data['user_id']))
        
        # Delete used token
        cursor.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
        
        conn.commit()
        
        print(f"Password reset successfully for user: {token_data['user_id']}")
        
        return {
            "success": True,
            "message": "Password reset successfully"
        }
        
    except Error as e:
        print(f"Database error: {e}")
        return {"error": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

def verify_reset_token(token):
    """Check if reset token is valid"""
    conn = create_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT u.email, u.name 
            FROM password_reset_tokens prt 
            JOIN users u ON prt.user_id = u.id 
            WHERE prt.token = %s AND prt.expires_at > NOW()
        """, (token,))
        
        token_data = cursor.fetchone()
        
        if not token_data:
            return {"error": "Invalid or expired token"}
        
        return {
            "valid": True,
            "email": token_data['email'],
            "name": token_data['name']
        }
        
    except Error as e:
        return {"error": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

def init_db():
    """Initialize database"""
    return initialize_db()
