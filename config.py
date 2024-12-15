import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 데이터베이스 설정 로드
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'test')
DB_PORT = int(os.getenv('DB_PORT', '3306'))

# JWT 및 인증 관련 설정
SECRET_KEY = os.getenv('SECRET_KEY', 'secret')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
