import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from routes.auth_routes import router as auth_router
from routes.jobs_routes import router as jobs_router
from routes.applications_routes import router as applications_router
from routes.bookmarks_routes import router as bookmarks_router

# 로거 설정
logger = logging.getLogger("api_logger")
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = FastAPI(
    title="Job API",
    description="Job recruitment API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 시 필요한 도메인으로 제한하는 것이 바람직
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(bookmarks_router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    모든 요청에 대해 로그를 남기는 미들웨어
    """
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        raise
    logger.info(f"Response status: {response.status_code}")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    전역 예외 처리 핸들러
    """
    logger.error(f"Global Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )

def custom_openapi():
    """
    OpenAPI 스키마 커스터마이징
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Job API",
        version="1.0.0",
        description="백정렬의 전북대학교 웹서비스설계 과제3 API입니다.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }

    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/auth/login",
                    "scopes": {}
                }
            }
        }
    }

    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi
