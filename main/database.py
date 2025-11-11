import mysql.connector
from mysql.connector import Error
from config import Config
from utils import hash_password, verify_password, generate_user_id, normalize_email

def create_connection():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            auth_plugin='mysql_native_password'
        )
        print("Database connection successful")
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
            # Login with User ID
            print(f"Searching by User ID: {user_id}")
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            identifier_type = "User ID"
            identifier_value = user_id
        else:
            # Login with Email
            email = normalize_email(email)
            print(f"Searching by normalized email: {email}")
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            identifier_type = "email"
            identifier_value = email
        
        if not user:
            print(f"User not found with {identifier_type}: {identifier_value}")
            return {"error": "User not found"}
        
        print(f"User found: {user['id']} - {user['name']}")
        
        # Verify password
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

def get_user_by_id(user_id):
    """Get user by user_id"""
    try:
        conn = create_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        return user
        
    except mysql.connector.Error as e:
        print(f"Error getting user by ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize database"""
    return initialize_db()