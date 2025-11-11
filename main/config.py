# All the important configuration value are defined here.
import os

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'your name')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your password')
    DB_NAME = os.getenv('DB_NAME', 'user_system')
    SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')

    SERVER_PORT = int(os.getenv('SERVER_PORT', '8080'))
