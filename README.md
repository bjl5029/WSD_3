# 웹서비스 설계 과제 3

## 프로젝트 개요
이 프로젝트는 **MySQL 데이터베이스**를 기반으로 Python **3.12**에서 개발된 백엔드 서비스임.
FastAPI를 사용하여 RESTful API를 제공하며, Swagger를 통해 API 문서를 제공.

백엔드 서버와 DB 서버를 분리하여 구성할 것을 상정하여 개발됨.

---

## 프로젝트 구조
```plaintext
.
├─ .env                      # 환경 변수 파일
├─ main.py                   # 진입점
├─ config.py                 # 설정 파일
├─ database.py               # DB 연결 및 초기화
├─ auth.py                   # 인증 관련 모듈
├─ models.py                 # 데이터베이스 모델
└─ routes                    # API
   ├─ auth_routes.py         # 인증 관련
   ├─ jobs_routes.py         # 채용 공고 관련
   ├─ applications_routes.py # 지원서 관련
   └─ bookmarks_routes.py    # 북마크 관련
```

---

## 환경 설정

### `.env` 파일 형식
다음과 같은 형식으로 `.env` 파일을 생성해야 함.:
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

## 라이브러리 설치
이 프로젝트의 종속성은 다음과 같음.:
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

종속성 설치는 다음 명령어로 실행할 수 있음.:
```bash
pip install -r requirements.txt
```

---

## 실행 및 Swagger 문서
- **애플리케이션 실행**:  
  ```bash
  uvicorn main:app --reload --port 8080 --host 0.0.0.0
  ```
- **Swagger 문서 확인**:  
  /docs

---

## API 엔드포인트

### 인증 API (`/auth`)
| 메서드 | 엔드포인트          | 설명                |
|--------|---------------------|---------------------|
| POST   | `/auth/register`    | 회원가입            |
| POST   | `/auth/login`       | 로그인              |
| POST   | `/auth/refresh`     | 토큰 갱신           |
| GET    | `/auth/profile`     | 회원 정보 조회      |
| PUT    | `/auth/profile`     | 회원 정보 수정      |
| DELETE | `/auth/delete`      | 회원 탈퇴           |

### 채용 공고 API (`/jobs`)
| 메서드 | 엔드포인트          | 설명                |
|--------|---------------------|---------------------|
| GET    | `/jobs`             | 채용 공고 조회      |
| POST   | `/jobs`             | 채용 공고 등록      |
| GET    | `/jobs/{id}`        | 채용 공고 상세 조회 |
| PUT    | `/jobs/{id}`        | 채용 공고 수정      |
| DELETE | `/jobs/{id}`        | 채용 공고 삭제      |

### 지원서 API (`/applications`)
| 메서드 | 엔드포인트          | 설명                |
|--------|---------------------|---------------------|
| POST   | `/applications`     | 지원하기            |
| GET    | `/applications`     | 지원 내역 조회      |
| DELETE | `/applications/{id}`| 지원 취소           |

### 북마크 API (`/bookmarks`)
| 메서드 | 엔드포인트          | 설명                |
|--------|---------------------|---------------------|
| POST   | `/bookmarks`        | 북마크 추가/제거    |
| GET    | `/bookmarks`        | 북마크 목록 조회    |

---

## DB 데이터 추가 스크립트: `crawling2db.py`
이 스크립트는 1시간에 한 번 씩 모든 검색 키워드 리스트를 pages 만큼 순회하며 크롤링 후 DB에 추가한다.
DB에 데이터 추가 시 중복된 데이터는 무시되며 크롤링 결과는 saramin_{keyword}.csv에, DB 데이터 추가 로그는 db_loader.log에 저장된다.


### 권장 실행 환경
- Python **3.11**
- **스크립트 종속성**:
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
---
