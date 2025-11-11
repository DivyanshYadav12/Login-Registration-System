# All the important configuration value are defined here.
import os

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'divyansh')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin123')
    DB_NAME = os.getenv('DB_NAME', 'user_system')
    SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
    SERVER_PORT = int(os.getenv('SERVER_PORT', '8080'))