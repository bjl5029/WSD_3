from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, List
from database import get_db
from models import JobCreate, JobUpdate
from auth import get_current_user, check_admin

router = APIRouter(tags=["jobs"], prefix="/jobs")

@router.get("", summary="채용 공고 조회")
def list_jobs(
    keyword: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    position: Optional[str] = Query(None),
    salary_info: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_categories: Optional[List[str]] = Query(None),
    tech_stacks: Optional[List[str]] = Query(None),
    sort: Optional[str] = Query("created_at_desc"),
    page: int = 1,
    db=Depends(get_db)
):
    """
    다양한 조건으로 채용 공고 목록 조회 (페이지네이션 정보 포함)
    """
    page_size = 20
    offset = (page - 1) * page_size

    # Base query (for data)
    base_query = """
    SELECT DISTINCT
        jp.posting_id,
        c.name AS company_name,
        jp.title,
        jp.job_description,
        jp.experience_level,
        jp.education_level,
        jp.employment_type,
        jp.salary_info,
        CONCAT(l.city, ' ', COALESCE(l.district, '')) AS location,
        jp.deadline_date,
        jp.view_count,
        GROUP_CONCAT(DISTINCT ts.name) AS tech_stacks,
        GROUP_CONCAT(DISTINCT jc.name) AS job_categories
    FROM job_postings jp
    JOIN companies c ON jp.company_id = c.company_id
    LEFT JOIN locations l ON jp.location_id = l.location_id
    LEFT JOIN posting_tech_stacks pts ON jp.posting_id = pts.posting_id
    LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
    LEFT JOIN posting_categories pc ON jp.posting_id = pc.posting_id
    LEFT JOIN job_categories jc ON pc.category_id = jc.category_id
    WHERE jp.status = 'active'
    """

    # 동일한 조건으로 total_count를 구하기 위한 쿼리 (COUNT DISTINCT)
    count_query = """
    SELECT COUNT(DISTINCT jp.posting_id) AS total_count
    FROM job_postings jp
    JOIN companies c ON jp.company_id = c.company_id
    LEFT JOIN locations l ON jp.location_id = l.location_id
    LEFT JOIN posting_tech_stacks pts ON jp.posting_id = pts.posting_id
    LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
    LEFT JOIN posting_categories pc ON jp.posting_id = pc.posting_id
    LEFT JOIN job_categories jc ON pc.category_id = jc.category_id
    WHERE jp.status = 'active'
    """

    params = []

    # 조건절 구성
    def add_condition(condition_str, values):
        nonlocal base_query, count_query, params
        base_query += condition_str
        count_query += condition_str
        params.extend(values)

    if keyword:
        add_condition(" AND (jp.title LIKE %s OR jp.job_description LIKE %s)", [f"%{keyword}%", f"%{keyword}%"])
    if company:
        add_condition(" AND c.name LIKE %s", [f"%{company}%"])
    if employment_type:
        add_condition(" AND jp.employment_type = %s", [employment_type])
    if position:
        add_condition(" AND jp.title LIKE %s", [f"%{position}%"])
    if salary_info:
        add_condition(" AND jp.salary_info LIKE %s", [f"%{salary_info}%"])
    if location:
        add_condition(" AND (l.city LIKE %s OR l.district LIKE %s)", [f"%{location}%", f"%{location}%"])
    if tech_stacks:
        placeholders = ','.join(['%s'] * len(tech_stacks))
        add_condition(f" AND ts.name IN ({placeholders})", tech_stacks)
    if job_categories:
        placeholders = ','.join(['%s'] * len(job_categories))
        add_condition(f" AND jc.name IN ({placeholders})", job_categories)

    # GROUP BY와 정렬 조건
    base_query += " GROUP BY jp.posting_id"
    if sort == "created_at_desc":
        base_query += " ORDER BY jp.created_at DESC"
    elif sort == "created_at_asc":
        base_query += " ORDER BY jp.created_at ASC"
    elif sort == "view_count_desc":
        base_query += " ORDER BY jp.view_count DESC"
    else:
        # 기본 정렬 기준 없을 경우 created_at DESC로
        base_query += " ORDER BY jp.created_at DESC"

    # 페이지네이션
    base_query += f" LIMIT {page_size} OFFSET {offset}"

    cursor = db.cursor(dictionary=True)

    # total_count 구하기
    cursor.execute(count_query, params)
    total_count_result = cursor.fetchone()
    total_count = total_count_result['total_count'] if total_count_result else 0

    # 실제 데이터 조회
    cursor.execute(base_query, params)
    jobs = cursor.fetchall()

    for job in jobs:
        job['tech_stacks'] = job['tech_stacks'].split(',') if job['tech_stacks'] else []
        job['job_categories'] = job['job_categories'].split(',') if job['job_categories'] else []

    cursor.close()

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return {
        "items": jobs,
        "total_count": total_count,
        "total_pages": total_pages,
        "page_size": page_size,
        "current_page": page
    }
