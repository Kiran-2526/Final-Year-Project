import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'agri_thermal_paddy_secret_key_2026')
    
    # MySQL Database Config
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'passwordMysql@52')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'paddy_disease_db')

    # Path Settings (Project Relative)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR = os.environ.get('UPLOAD_DIR', os.path.join(BASE_DIR, 'uploads'))
    MODEL_PATH = os.environ.get('MODEL_PATH', os.path.join(BASE_DIR, 'ml', 'models', 'best_model.pth'))
