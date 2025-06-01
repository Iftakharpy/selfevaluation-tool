from fastapi import Depends, HTTPException, status, Request
from passlib.context import CryptContext
from typing import Optional
from bson import ObjectId

from .data_types import UserInDB, UserOut, PyObjectId, RoleEnum # MODIFIED: Added RoleEnum
from app.core.db import get_user_collection
from app.core.settings import PWD_ALGORITHM


# Password Hashing
pwd_context = CryptContext(schemes=[PWD_ALGORITHM], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Authentication / Session Dependencies
async def get_current_user_from_session(request: Request) -> Optional[UserInDB]:
    user_id_str = request.session.get("user_id")
    if not user_id_str:
        return None
    
    if not ObjectId.is_valid(user_id_str):
        request.session.clear()
        return None
    
    user_collection = get_user_collection()
    try:
        user_dict = await user_collection.find_one({"_id": ObjectId(user_id_str)})
    except Exception:
        return None
        
    if user_dict:
        return UserInDB(**user_dict)
    return None

async def get_current_active_user(
    current_user: Optional[UserInDB] = Depends(get_current_user_from_session)
) -> UserInDB:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Session"},
        )
    return current_user

# MODIFIED: Added role-based dependency
async def require_teacher_role(current_user: UserInDB = Depends(get_current_active_user)):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Teacher role required."
        )
    return current_user
# END MODIFICATION

def to_user_out(user_in_db: UserInDB) -> UserOut:
    user_data_for_out = user_in_db.model_dump(by_alias=False, exclude={'password_hash'})

    if 'id' in user_data_for_out and isinstance(user_data_for_out['id'], PyObjectId):
        user_data_for_out['id'] = str(user_data_for_out['id'])
    
    return UserOut(**user_data_for_out)