# 프로젝트 README

## 📘 프로젝트 개요
이 프로젝트는 **MySQL 데이터베이스**를 기반으로 Python **3.12**에서 개발된 백엔드 서비스입니다.  
FastAPI를 사용하여 RESTful API를 제공하며, Swagger를 통해 API 문서를 제공합니다.  

---

## 🗂️ 프로젝트 구조
```plaintext
.
├─ .env                      # 환경 변수 파일
├─ main.py                   # 프로젝트 진입점
├─ config.py                 # 설정 파일
├─ database.py               # DB 연결 및 초기화
├─ auth.py                   # 인증 관련 모듈
├─ models.py                 # 데이터베이스 모델
└─ routes                    # API 라우터 폴더
   ├─ auth_routes.py         # 인증 관련 라우터
   ├─ jobs_routes.py         # 채용 공고 관련 라우터
   ├─ applications_routes.py # 지원서 관련 라우터
   └─ bookmarks_routes.py    # 북마크 관련 라우터
```

---

## ⚙️ 환경 설정

### `.env` 파일 형식
다음과 같은 형식으로 `.env` 파일을 생성해야 합니다:
```plaintext
DB_HOST=000.000.00.00
DB_USER=DB username
DB_PASSWORD=DB password
DB_NAME=DB name
DB_PORT=DB port

SECRET_KEY=secret key
ALGORITHM=hash algorithm
ACCESS_TOKEN_EXPIRE_MINUTES=access 토큰 만료 시간
REFRESH_TOKEN_EXPIRE_DAYS=refresh 토큰 만료 시간
```

---

## 📦 의존성 설치
### 필수 라이브러리
다음은 이 프로젝트에서 사용된 Python 패키지들입니다:
```plaintext
annotated-types==0.7.0
anyio==4.6.2.post1
cffi==1.17.1
click==8.1.7
cryptography==44.0.0
dnspython==2.7.0
ecdsa==0.19.0
email_validator==2.2.0
fastapi==0.115.6
h11==0.14.0
idna==3.10
mysql-connector-python==9.1.0
passlib==1.7.4
pyasn1==0.6.1
pycparser==2.22
pydantic==2.10.2
pydantic-settings==2.6.1
pydantic_core==2.27.1
python-dotenv==1.0.1
python-jose==3.3.0
python-multipart==0.0.19
rsa==4.9
six==1.16.0
sniffio==1.3.1
starlette==0.41.3
typing_extensions==4.12.2
uvicorn==0.32.1
```

의존성 설치는 다음 명령어로 실행할 수 있습니다:
```bash
pip install -r requirements.txt
```

---

## 🚀 실행 및 Swagger 문서
- **애플리케이션 실행**:  
  ```bash
  python main.py
  ```
- **Swagger 문서 확인**:  
  [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔗 API 엔드포인트

### 🛡️ 인증 API (`/auth`)
| 메서드 | 엔드포인트          | 설명                |
|--------|---------------------|---------------------|
| POST   | `/auth/register`    | 회원가입            |
| POST   | `/auth/login`       | 로그인              |
| POST   | `/auth/refresh`     | 토큰 갱신           |
| GET    | `/auth/profile`     | 회원 정보 조회      |
| PUT    | `/auth/profile`     | 회원 정보 수정      |
| DELETE | `/auth/delete`      | 회원 탈퇴           |

### 💼 채용 공고 API (`/jobs`)
| 메서드 | 엔드포인트          | 설명                |
|--------|---------------------|---------------------|
| GET    | `/jobs`             | 채용 공고 조회      |
| POST   | `/jobs`             | 채용 공고 등록      |
| GET    | `/jobs/{id}`        | 채용 공고 상세 조회 |
| PUT    | `/jobs/{id}`        | 채용 공고 수정      |
| DELETE | `/jobs/{id}`        | 채용 공고 삭제      |

### 📝 지원서 API (`/applications`)
| 메서드 | 엔드포인트          | 설명                |
|--------|---------------------|---------------------|
| POST   | `/applications`     | 지원하기            |
| GET    | `/applications`     | 지원 내역 조회      |
| DELETE | `/applications/{id}`| 지원 취소           |

### ⭐ 북마크 API (`/bookmarks`)
| 메서드 | 엔드포인트          | 설명                |
|--------|---------------------|---------------------|
| POST   | `/bookmarks`        | 북마크 추가/제거    |
| GET    | `/bookmarks`        | 북마크 목록 조회    |

---

## 🌐 DB 데이터 추가 스크립트: `crawling2db.py`
이 스크립트는 지정된 키워드를 검색하여 데이터를 크롤링하고, MySQL DB에 저장합니다.  

### 실행 환경
- Python **3.11**
- **추가 의존성**:
  ```plaintext
  beautifulsoup4==4.12.3
  certifi==2024.12.14
  charset-normalizer==3.4.0
  idna==3.10
  mysql-connector-python==9.1.0
  numpy==2.2.0
  pandas==2.2.3
  python-dateutil==2.9.0.post0
  pytz==2024.2
  requests==2.32.3
  six==1.17.0
  soupsieve==2.6
  tzdata==2024.2
  urllib3==2.2.3
  ```

### 실행 방법
```bash
python crawling2db.py --keywords {검색 키워드 리스트(space separated values)} --pages {페이지}
```

### 작동 방식
- **1시간에 한 번** 검색 키워드와 페이지 수를 기준으로 데이터를 크롤링 후 MySQL DB에 추가합니다.
- **중복 데이터 무시**: 이미 DB에 존재하는 데이터는 추가되지 않습니다.
- 크롤링 결과: `saramin_{keyword}.csv` 파일 저장
- 로그: `db_loader.log`에 저장

---

## 📜 주의 사항
- `.env` 파일을 반드시 설정해야 애플리케이션이 정상적으로 작동합니다.
- 크롤링 스크립트와 메인 프로젝트의 Python 버전이 다르므로 실행 환경을 구분하세요.

---

## 📧 문의
문제가 발생하거나 추가 문의사항이 있다면 [이메일](mailto:your_email@example.com)로 연락해주세요.  
즐거운 개발 시간 되시길 바랍니다! 🚀
