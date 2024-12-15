from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, Query
from typing import Optional
import datetime
from database import get_db
from auth import get_current_user

router = APIRouter(tags=["applications"], prefix="/applications")

@router.post("", summary="지원하기")
async def apply_for_job(
    posting_id: int = Form(...),
    resume_id: Optional[int] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    특정 채용 공고에 지원하기.
    resume_id나 resume_file 둘 중 하나는 반드시 필요.
    """
    cursor = db.cursor(dictionary=True)
    # 이미 지원했는지 확인
    cursor.execute(
        "SELECT application_id FROM applications WHERE user_id=%s AND posting_id=%s",
        (current_user['user_id'], posting_id)
    )
    if cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=400, detail="Already applied for this job posting.")

    if not resume_id and not resume_file:
        cursor.close()
        raise HTTPException(status_code=400, detail="Either resume_id or resume_file must be provided.")

    # 업로드 파일이 있는 경우 PDF 검사 후 DB 삽입
    if resume_file:
        if resume_file.content_type != "application/pdf":
            cursor.close()
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        file_content = await resume_file.read()
        cursor.execute(
            "INSERT INTO resumes(user_id, title, content, is_primary) VALUES(%s, %s, %s, 0)",
            (current_user['user_id'], f"Uploaded Resume {datetime.datetime.utcnow()}", file_content)
        )
        db.commit()
        resume_id = cursor.lastrowid

    if resume_id:
        cursor.execute("SELECT resume_id,user_id FROM resumes WHERE resume_id=%s", (resume_id,))
        r = cursor.fetchone()
        if not r or r['user_id'] != current_user['user_id']:
            cursor.close()
            raise HTTPException(status_code=403, detail="Not authorized to use this resume or it doesn't exist.")

    cursor.execute(
        "INSERT INTO applications(user_id, posting_id, resume_id, status) VALUES (%s, %s, %s, 'pending')",
        (current_user['user_id'], posting_id, resume_id)
    )
    db.commit()
    application_id = cursor.lastrowid
    cursor.close()

    return {"detail": "Application submitted successfully", "application_id": application_id}

@router.delete("/{id}", summary="지원 취소")
def cancel_application(id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    """
    지원 취소 (applications 레코드 삭제)
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM applications WHERE application_id=%s", (id,))
    appl = cursor.fetchone()
    if not appl:
        cursor.close()
        raise HTTPException(status_code=404, detail="Application not found")
    if appl['user_id'] != current_user['user_id']:
        cursor.close()
        raise HTTPException(status_code=403, detail="Not your application")

    cursor.execute("DELETE FROM applications WHERE application_id=%s", (id,))
    db.commit()
    cursor.close()
    return {"detail": "Application canceled"}

@router.get("", summary="지원 내역 조회")
def list_applications(
    status_filter: Optional[str] = Query(None, description="pending, reviewed, accepted, rejected"),
    sort_by_date: Optional[str] = Query("desc"),
    page: int = 1,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    로그인한 사용자의 지원 내역 조회
    """
    query = """
    SELECT a.application_id, a.posting_id, jp.title, a.status, a.applied_at
    FROM applications a
    JOIN job_postings jp ON a.posting_id=jp.posting_id
    WHERE a.user_id=%s
    """
    params = [current_user['user_id']]
    if status_filter:
        query += " AND a.status=%s"
        params.append(status_filter)

    query += " ORDER BY a.applied_at " + ("ASC" if sort_by_date == "asc" else "DESC")

    page_size = 20
    offset = (page - 1) * page_size
    query += f" LIMIT {page_size} OFFSET {offset}"

    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    apps = cursor.fetchall()
    cursor.close()
    return apps
