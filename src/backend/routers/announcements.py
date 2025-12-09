"""
Announcement管理API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)

# 認証・権限チェック

def require_auth(username: str) -> Dict[str, Any]:
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="認証が必要です")
    if teacher["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="権限がありません")
    return teacher

@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_announcements() -> List[Dict[str, Any]]:
    """有効な全お知らせを取得（期限切れは除外）"""
    now = datetime.utcnow().strftime('%Y-%m-%d')
    announcements = []
    for ann in announcements_collection.find({"expiration_date": {"$gte": now}}):
        ann["id"] = str(ann.get("_id", ""))
        ann.pop("_id", None)
        announcements.append(ann)
    return announcements

@router.post("/add")
def add_announcement(message: str, expiration_date: str, start_date: Optional[str] = None, teacher_username: str = Query(...)):
    """お知らせ追加（認証必須）"""
    require_auth(teacher_username)
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    ann = {
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_at": now,
        "updated_at": now
    }
    result = announcements_collection.insert_one(ann)
    return {"id": str(result.inserted_id), "message": "追加しました"}

@router.put("/update/{announcement_id}")
def update_announcement(announcement_id: str, message: Optional[str] = None, expiration_date: Optional[str] = None, start_date: Optional[str] = None, teacher_username: str = Query(...)):
    """お知らせ編集（認証必須）"""
    require_auth(teacher_username)
    update_fields = {"updated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}
    if message is not None:
        update_fields["message"] = message
    if expiration_date is not None:
        update_fields["expiration_date"] = expiration_date
    if start_date is not None:
        update_fields["start_date"] = start_date
    result = announcements_collection.update_one({"_id": announcement_id}, {"$set": update_fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="お知らせが見つかりません")
    return {"message": "更新しました"}

@router.delete("/delete/{announcement_id}")
def delete_announcement(announcement_id: str, teacher_username: str = Query(...)):
    """お知らせ削除（認証必須）"""
    require_auth(teacher_username)
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="お知らせが見つかりません")
    return {"message": "削除しました"}
