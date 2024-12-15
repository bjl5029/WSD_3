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
    다양한 조건으로 채용 공고 목록 조회
    """
    # 쿼리 작성 및 조건 처리
    query = """
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

    params = []
    if keyword:
        query += " AND (jp.title LIKE %s OR jp.job_description LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if company:
        query += " AND c.name LIKE %s"
        params.append(f"%{company}%")
    if employment_type:
        query += " AND jp.employment_type = %s"
        params.append(employment_type)
    if position:
        query += " AND jp.title LIKE %s"
        params.append(f"%{position}%")
    if salary_info:
        query += " AND jp.salary_info LIKE %s"
        params.append(f"%{salary_info}%")
    if location:
        query += " AND (l.city LIKE %s OR l.district LIKE %s)"
        params.extend([f"%{location}%", f"%{location}%"])
    if tech_stacks:
        query += " AND ts.name IN (" + ','.join(['%s'] * len(tech_stacks)) + ")"
        params.extend(tech_stacks)
    if job_categories:
        query += " AND jc.name IN (" + ','.join(['%s'] * len(job_categories)) + ")"
        params.extend(job_categories)

    query += " GROUP BY jp.posting_id"

    if sort == "created_at_desc":
        query += " ORDER BY jp.created_at DESC"
    elif sort == "created_at_asc":
        query += " ORDER BY jp.created_at ASC"
    elif sort == "view_count_desc":
        query += " ORDER BY jp.view_count DESC"

    page_size = 20
    offset = (page - 1) * page_size
    query += f" LIMIT {page_size} OFFSET {offset}"

    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    jobs = cursor.fetchall()

    for job in jobs:
        job['tech_stacks'] = job['tech_stacks'].split(',') if job['tech_stacks'] else []
        job['job_categories'] = job['job_categories'].split(',') if job['job_categories'] else []

    cursor.close()
    return jobs

@router.get("/{id}", summary="채용 공고 상세 조회")
def get_job_detail(id: int = Path(...), db=Depends(get_db)):
    """
    특정 채용 공고 상세 정보 조회 및 연관 공고 조회
    """
    cursor = db.cursor(dictionary=True)
    # 조회수 증가
    cursor.execute("UPDATE job_postings SET view_count = view_count + 1 WHERE posting_id = %s", (id,))
    db.commit()

    query = """
    SELECT 
        jp.*,
        c.name as company_name,
        l.city,
        l.district,
        GROUP_CONCAT(DISTINCT ts.name) as tech_stacks,
        GROUP_CONCAT(DISTINCT jc.name) as job_categories
    FROM job_postings jp
    JOIN companies c ON jp.company_id = c.company_id
    LEFT JOIN locations l ON jp.location_id = l.location_id
    LEFT JOIN posting_tech_stacks pts ON jp.posting_id = pts.posting_id
    LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
    LEFT JOIN posting_categories pc ON jp.posting_id = pc.posting_id
    LEFT JOIN job_categories jc ON pc.category_id = jc.category_id
    WHERE jp.posting_id = %s AND jp.status != 'deleted'
    GROUP BY jp.posting_id
    """
    cursor.execute(query, (id,))
    job = cursor.fetchone()

    if not job:
        cursor.close()
        raise HTTPException(status_code=404, detail="Job not found")

    job['tech_stacks'] = job['tech_stacks'].split(',') if job['tech_stacks'] else []
    job['job_categories'] = job['job_categories'].split(',') if job['job_categories'] else []

    related_query = """
    SELECT DISTINCT jp.posting_id, jp.title, c.name as company_name
    FROM job_postings jp
    JOIN companies c ON jp.company_id = c.company_id
    LEFT JOIN posting_tech_stacks pts ON jp.posting_id = pts.posting_id
    LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
    WHERE jp.status = 'active' 
    AND jp.posting_id != %s
    AND (
        jp.company_id = %s 
        OR ts.name IN (
            SELECT ts2.name 
            FROM posting_tech_stacks pts2 
            JOIN tech_stacks ts2 ON pts2.stack_id = ts2.stack_id 
            WHERE pts2.posting_id = %s
        )
    )
    ORDER BY RAND()
    LIMIT 5
    """

    cursor.execute(related_query, (id, job['company_id'], id))
    related = cursor.fetchall()
    cursor.close()

    return {"job": job, "related": related}

@router.post("", summary="채용 공고 등록")
def create_job(job: JobCreate, current_user=Depends(check_admin), db=Depends(get_db)):
    """
    관리자 전용 채용 공고 등록
    """
    cursor = db.cursor(dictionary=True)
    try:
        location_id = None
        if job.location:
            cursor.execute(
                "SELECT location_id FROM locations WHERE city = %s AND (district = %s OR (district IS NULL AND %s IS NULL))",
                (job.location.city, job.location.district, job.location.district)
            )
            location_result = cursor.fetchone()

            if location_result:
                location_id = location_result['location_id']
            else:
                cursor.execute(
                    "INSERT INTO locations (city, district) VALUES (%s, %s)",
                    (job.location.city, job.location.district)
                )
                location_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO job_postings(
                company_id, title, job_description, experience_level,
                education_level, employment_type, salary_info,
                location_id, deadline_date, status, view_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', 0)
            """,
            (
                job.company_id, job.title, job.job_description,
                job.experience_level, job.education_level,
                job.employment_type, job.salary_info,
                location_id, job.deadline_date
            )
        )
        posting_id = cursor.lastrowid

        # 기술 스택 처리
        if job.tech_stacks:
            for tech in job.tech_stacks:
                cursor.execute("SELECT stack_id FROM tech_stacks WHERE name = %s", (tech,))
                result = cursor.fetchone()
                if not result:
                    cursor.execute("INSERT INTO tech_stacks (name, category) VALUES (%s, 'Other')", (tech,))
                    stack_id = cursor.lastrowid
                else:
                    stack_id = result['stack_id']

                cursor.execute(
                    "INSERT INTO posting_tech_stacks (posting_id, stack_id) VALUES (%s, %s)",
                    (posting_id, stack_id)
                )

        # 직무 카테고리 처리
        if job.job_categories:
            for category in job.job_categories:
                cursor.execute("SELECT category_id FROM job_categories WHERE name = %s", (category,))
                result = cursor.fetchone()
                if not result:
                    cursor.execute("INSERT INTO job_categories (name) VALUES (%s)", (category,))
                    category_id = cursor.lastrowid
                else:
                    category_id = result['category_id']

                cursor.execute(
                    "INSERT INTO posting_categories (posting_id, category_id) VALUES (%s, %s)",
                    (posting_id, category_id)
                )

        db.commit()
        return {"detail": "Job posting created successfully", "posting_id": posting_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.put("/{id}", summary="채용 공고 수정")
def update_job(id: int, job: JobUpdate, current_user=Depends(check_admin), db=Depends(get_db)):
    """
    관리자 전용 채용 공고 수정
    """
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT posting_id FROM job_postings WHERE posting_id = %s", (id,))
        existing_job = cursor.fetchone()
        if not existing_job:
            raise HTTPException(status_code=404, detail="Job posting not found")

        updates = {}
        if job.title is not None:
            updates["title"] = job.title
        if job.job_description is not None:
            updates["job_description"] = job.job_description
        if job.experience_level is not None:
            updates["experience_level"] = job.experience_level
        if job.education_level is not None:
            updates["education_level"] = job.education_level
        if job.employment_type is not None:
            updates["employment_type"] = job.employment_type
        if job.salary_info is not None:
            updates["salary_info"] = job.salary_info
        if job.deadline_date is not None:
            updates["deadline_date"] = job.deadline_date
        if job.status is not None:
            updates["status"] = job.status.value

        if job.location:
            cursor.execute(
                "SELECT location_id FROM locations WHERE city = %s AND (district = %s OR (district IS NULL AND %s IS NULL))",
                (job.location.city, job.location.district, job.location.district)
            )
            location_result = cursor.fetchone()
            if location_result:
                updates["location_id"] = location_result['location_id']
            else:
                cursor.execute(
                    "INSERT INTO locations (city, district) VALUES (%s, %s)",
                    (job.location.city, job.location.district)
                )
                updates["location_id"] = cursor.lastrowid

        if updates:
            set_clause = ", ".join(f"{key} = %s" for key in updates)
            cursor.execute(f"UPDATE job_postings SET {set_clause} WHERE posting_id = %s",
                           list(updates.values()) + [id])

        # 기술 스택 재설정
        if job.tech_stacks is not None:
            cursor.execute("DELETE FROM posting_tech_stacks WHERE posting_id = %s", (id,))
            for tech in job.tech_stacks:
                cursor.execute("SELECT stack_id FROM tech_stacks WHERE name = %s", (tech,))
                result = cursor.fetchone()
                if not result:
                    cursor.execute("INSERT INTO tech_stacks (name) VALUES (%s)", (tech,))
                    stack_id = cursor.lastrowid
                else:
                    stack_id = result['stack_id']
                cursor.execute(
                    "INSERT INTO posting_tech_stacks (posting_id, stack_id) VALUES (%s, %s)",
                    (id, stack_id)
                )

        # 직무 카테고리 재설정
        if job.job_categories is not None:
            cursor.execute("DELETE FROM posting_categories WHERE posting_id = %s", (id,))
            for category in job.job_categories:
                cursor.execute("SELECT category_id FROM job_categories WHERE name = %s", (category,))
                result = cursor.fetchone()
                if not result:
                    cursor.execute("INSERT INTO job_categories (name) VALUES (%s)", (category,))
                    category_id = cursor.lastrowid
                else:
                    category_id = result['category_id']
                cursor.execute(
                    "INSERT INTO posting_categories (posting_id, category_id) VALUES (%s, %s)",
                    (id, category_id)
                )

        db.commit()
        return {"detail": "Job posting updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.delete("/{id}", summary="채용 공고 삭제")
def delete_job(id: int, current_user=Depends(check_admin), db=Depends(get_db)):
    """
    관리자 전용 채용 공고 삭제 (status를 deleted로 변경)
    """
    cursor = db.cursor()
    cursor.execute("UPDATE job_postings SET status='deleted' WHERE posting_id=%s", (id,))
    db.commit()
    cursor.close()
    return {"detail": "Job deleted"}
