from mysql.connector import pooling
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT

# DB 풀 생성
db_pool = pooling.MySQLConnectionPool(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    port=DB_PORT
)

def get_db():
    """
    데이터베이스 커넥션을 제공하는 종속성 함수.
    요청 종료 후 커넥션을 반환한다.
    """
    conn = db_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()
