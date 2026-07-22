import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import UserOut, UserUpdate
from app.routers.auth import get_current_user
from app.utils.security import get_password_hash
from app.config import settings

router = APIRouter(prefix="/users", tags=["users"])

@router.put("/me", response_model=UserOut)
def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
        
    if user_update.email is not None:
        # Check if email taken
        if user_update.email != current_user.email:
            existing = db.query(User).filter(User.email == user_update.email).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email address is already registered."
                )
            current_user.email = user_update.email
            
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
        
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/avatar", response_model=UserOut)
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats: PNG, JPG, JPEG"
        )
        
    # Create unique filename
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = os.path.join(settings.MEDIA_STORAGE_PATH, "profile_pics", filename)
    
    # Save the file
    try:
        with open(file_path, "wb") as f:
            content = file.file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save profile picture: {str(e)}"
        )
        
    # Delete old avatar if it exists
    if current_user.profile_pic_url:
        old_path = current_user.profile_pic_url.replace(f"{settings.API_V1_STR}/users/avatar/static/", "")
        old_full_path = os.path.join(settings.MEDIA_STORAGE_PATH, "profile_pics", old_path)
        if os.path.exists(old_full_path):
            try:
                os.remove(old_full_path)
            except Exception:
                pass
                
    # Update DB URL
    current_user.profile_pic_url = f"{settings.API_V1_STR}/users/avatar/static/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user
