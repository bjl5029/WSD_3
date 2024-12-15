from datetime import date, timedelta
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, EmailStr

# 사용자 회원가입 모델
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    birth_date: Optional[date] = None

# 사용자 프로필 수정 모델
class UserProfile(BaseModel):
    name: str
    phone: Optional[str] = None
    birth_date: Optional[date] = None

# 토큰 응답 모델
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# 위치 정보 모델
class LocationCreate(BaseModel):
    city: str
    district: Optional[str] = None

# 채용공고 상태 Enum
class JobStatus(str, Enum):
    ACTIVE = 'active'
    CLOSED = 'closed'
    DELETED = 'deleted'

# 채용 공고 생성 모델
class JobCreate(BaseModel):
    company_id: int
    title: str
    job_description: str
    experience_level: Optional[str] = None
    education_level: Optional[str] = None
    employment_type: Optional[str] = None
    salary_info: Optional[str] = None
    location: Optional[LocationCreate] = None
    deadline_date: Optional[str] = None
    tech_stacks: Optional[List[str]] = None
    job_categories: Optional[List[str]] = None

# 채용 공고 업데이트 모델
class JobUpdate(BaseModel):
    company_id: Optional[int] = None
    title: Optional[str] = None
    job_description: Optional[str] = None
    experience_level: Optional[str] = None
    education_level: Optional[str] = None
    employment_type: Optional[str] = None
    salary_info: Optional[str] = None
    location: Optional[LocationCreate] = None
    deadline_date: Optional[str] = None
    status: Optional[JobStatus] = None
    tech_stacks: Optional[List[str]] = None
    job_categories: Optional[List[str]] = None

# 채용 공고 응답 모델
class JobResponse(BaseModel):
    posting_id: int
    company_name: str
    title: str
    job_description: Optional[str]
    experience_level: Optional[str]
    education_level: Optional[str]
    employment_type: Optional[str]
    salary_info: Optional[str]
    location: Optional[str]
    deadline_date: Optional[str]
    view_count: int
    tech_stacks: List[str]
    job_categories: List[str]

# 지원 생성 모델
class ApplicationCreate(BaseModel):
    posting_id: int
    resume_id: int

# 북마크 토글 모델
class BookmarkToggle(BaseModel):
    posting_id: int
