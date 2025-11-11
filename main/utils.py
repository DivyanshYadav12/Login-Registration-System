import re
import hashlib
import os
import uuid
from datetime import datetime

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def normalize_email(email):
    return email.strip().lower()

def hash_password(password):
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"

def verify_password(stored_hash, password):
    try:
        salt, original_hash = stored_hash.split("$", 1)
        new_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return new_hash == original_hash
    except:
        return False

"""unique user ID Generation like USR-ED36243C"""
def generate_user_id():
    return "USR-" + str(uuid.uuid4())[:8].upper()

def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def validate_password_strength(password):
    if not password:
        return False, "Password cannot be empty"
    
    # Check minimum length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for uppercase letters
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for lowercase letters
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for digits
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    # Check for special characters
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&* etc.)"
    
    # Check for common weak passwords (basic check)
    weak_passwords = ['password', '12345678', 'qwerty', 'admin', 'letmein']
    if password.lower() in weak_passwords:
        return False, "Password is too common and easily guessable"
    
    return True, "Password is strong"