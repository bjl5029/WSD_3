from fastapi import APIRouter, Depends, Query
from typing import Optional
from database import get_db
from auth import get_current_user
from models import BookmarkToggle

router = APIRouter(tags=["bookmarks"], prefix="/bookmarks")

@router.post("", summary="북마크 추가/제거")
def toggle_bookmark(bm: BookmarkToggle, current_user=Depends(get_current_user), db=Depends(get_db)):
    """
    특정 공고에 북마크 추가 혹은 제거
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT bookmark_id FROM bookmarks WHERE user_id=%s AND posting_id=%s",
        (current_user['user_id'], bm.posting_id)
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute("DELETE FROM bookmarks WHERE bookmark_id=%s", (existing['bookmark_id'],))
        db.commit()
        cursor.close()
        return {"detail": "Bookmark removed"}
    else:
        cursor.execute(
            "INSERT INTO bookmarks(user_id, posting_id) VALUES(%s,%s)",
            (current_user['user_id'], bm.posting_id)
        )
        db.commit()
        cursor.close()
        return {"detail": "Bookmark added"}

@router.get("", summary="북마크 목록 조회")
def list_bookmarks(
    page: int = 1,
    sort: str = "desc",
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    로그인한 사용자의 북마크 목록 조회
    """
    query = """
    SELECT 
        b.bookmark_id, 
        b.posting_id, 
        jp.title,
        jp.job_description,
        jp.experience_level,
        jp.education_level,
        jp.employment_type,
        jp.salary_info,
        CONCAT(l.city, ' ', COALESCE(l.district, '')) as location,
        jp.deadline_date,
        jp.view_count,
        c.name as company_name,
        GROUP_CONCAT(DISTINCT ts.name) as tech_stacks,
        GROUP_CONCAT(DISTINCT jc.name) as job_categories
    FROM bookmarks b
    JOIN job_postings jp ON b.posting_id = jp.posting_id
    JOIN companies c ON jp.company_id = c.company_id
    LEFT JOIN locations l ON jp.location_id = l.location_id
    LEFT JOIN posting_tech_stacks pts ON jp.posting_id = pts.posting_id
    LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
    LEFT JOIN posting_categories pc ON jp.posting_id = pc.posting_id
    LEFT JOIN job_categories jc ON pc.category_id = jc.category_id
    WHERE b.user_id = %s
    GROUP BY b.bookmark_id
    """
    query += " ORDER BY b.created_at " + ("ASC" if sort == "asc" else "DESC")

    page_size = 20
    offset = (page - 1) * page_size
    query += f" LIMIT {page_size} OFFSET {offset}"

    cursor = db.cursor(dictionary=True)
    cursor.execute(query, (current_user['user_id'],))
    bookmarks = cursor.fetchall()

    for bookmark in bookmarks:
        bookmark['tech_stacks'] = bookmark['tech_stacks'].split(',') if bookmark['tech_stacks'] else []
        bookmark['job_categories'] = bookmark['job_categories'].split(',') if bookmark['job_categories'] else []

    cursor.close()
    return bookmarks
