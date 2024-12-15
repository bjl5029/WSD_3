from fastapi import APIRouter, Depends, HTTPException, Body, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime
from database import get_db
from models import UserRegister, UserProfile, Token
from auth import verify_password, create_access_token, create_refresh_token, get_current_user

router = APIRouter(tags=["auth"], prefix="/auth")

@router.post("/register", response_model=Token, summary="회원가입")
def register_user(user: UserRegister, db=Depends(get_db)):
    """
    회원가입 엔드포인트
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM users WHERE email=%s", (user.email,))
    if cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    from auth import base64_encode_password
    hashed_pw = base64_encode_password(user.password)
    cursor.execute(
        "INSERT INTO users(email, password_hash, name, phone, birth_date, status) VALUES (%s,%s,%s,%s,%s,'active')",
        (user.email, hashed_pw, user.name, user.phone, user.birth_date)
    )
    db.commit()
    user_id = cursor.lastrowid
    cursor.close()

    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/login", response_model=Token, summary="로그인")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """
    로그인 엔드포인트
    """
    email = form_data.username
    password = form_data.password

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user_id, password_hash, status FROM users WHERE email=%s", (email,))
    db_user = cursor.fetchone()
    cursor.close()

    if not db_user or db_user['status'] != 'active':
        raise HTTPException(status_code=401, detail="Invalid credentials")

    from auth import verify_password
    if not verify_password(password, db_user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(db_user['user_id'])})
    refresh_token = create_refresh_token(data={"sub": str(db_user['user_id'])})

    cursor = db.cursor()
    cursor.execute("UPDATE users SET last_login=NOW() WHERE user_id=%s", (db_user['user_id'],))
    db.commit()
    cursor.close()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token, summary="토큰 갱신")
def refresh_token(token: str = Body(...), db=Depends(get_db)):
    """
    리프레시 토큰을 통한 액세스 토큰 재발급
    """
    from auth import create_access_token, create_refresh_token, SECRET_KEY, ALGORITHM
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("scope") != "refresh_token":
            raise HTTPException(status_code=401, detail="Invalid token scope.")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token.")

        try:
            user_id = int(user_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid token subject")

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT user_id,status FROM users WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()
        cursor.close()

        if not user or user['status'] != 'active':
            raise HTTPException(status_code=403, detail="User not active or does not exist")

        access_token = create_access_token(data={"sub": str(user_id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user_id)})
        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")

@router.put("/profile", summary="회원 정보 수정")
def update_profile(profile: UserProfile, current_user=Depends(get_current_user), db=Depends(get_db)):
    """
    회원 프로필 수정
    """
    cursor = db.cursor()
    cursor.execute(
        "UPDATE users SET name=%s, phone=%s, birth_date=%s WHERE user_id=%s",
        (profile.name, profile.phone, profile.birth_date, current_user['user_id'])
    )
    db.commit()
    cursor.close()
    return {"detail": "Profile updated"}

@router.get("/profile", summary="회원 정보 조회")
def get_profile(current_user=Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    """
    return {
        "user_id": current_user['user_id'],
        "email": current_user['email'],
        "name": current_user['name'],
        "phone": current_user['phone'],
        "birth_date": current_user['birth_date'],
        "status": current_user['status']
    }

@router.delete("/delete", summary="회원 탈퇴")
def delete_user(current_user=Depends(get_current_user), db=Depends(get_db)):
    """
    회원 탈퇴 (상태 inactive로 업데이트)
    """
    cursor = db.cursor()
    cursor.execute("UPDATE users SET status='inactive' WHERE user_id=%s", (current_user['user_id'],))
    db.commit()
    cursor.close()
    return {"detail": "User deactivated"}
