import base64
import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def base64_encode_password(raw_password: str) -> str:
    """
    패스워드를 Base64로 인코딩하는 유틸 함수
    """
    return base64.b64encode(raw_password.encode('utf-8')).decode('utf-8')

def verify_password(plain: str, encoded: str) -> bool:
    """
    평문 패스워드와 인코딩된 패스워드 검증
    """
    return base64_encode_password(plain) == encoded

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    액세스 토큰 생성
    """
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """
    리프레시 토큰 생성
    """
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "scope": "refresh_token"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    """
    현재 인증된 사용자 정보를 반환하는 종속성.
    토큰 검증 후 사용자 DB 조회.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        try:
            user_id = int(user_id)
        except ValueError:
            raise credentials_exception

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, email, name, status, phone, birth_date FROM users WHERE user_id=%s",
            (user_id,)
        )
        user = cursor.fetchone()
        cursor.close()

        if not user or user['status'] in ['inactive', 'blocked']:
            raise HTTPException(status_code=403, detail="User is not active.")

        return user
    except JWTError:
        raise credentials_exception

async def check_admin(user=Depends(get_current_user)):
    """
    관리자 권한 확인. user_id = 1인 경우 관리자라고 가정.
    """
    if user['user_id'] != 1:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user
