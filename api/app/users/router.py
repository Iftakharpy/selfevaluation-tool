# users/routes.py
from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from bson import ObjectId # For converting string ID from session to ObjectId for DB query

from .data_types import UserCreate, UserLogin, UserOut, UserInDB # Relative imports
from .auth import ( # Relative imports
    get_password_hash, 
    verify_password,
    get_current_active_user,
    to_user_out
)
from app.core.db import get_user_collection # Absolute import from project root

UserRouter = APIRouter()

@UserRouter.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup_user(user_in: UserCreate, request: Request):
    user_collection = get_user_collection()
    existing_user = await user_collection.find_one({"username": user_in.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username (email) already registered."
        )
    
    hashed_password = get_password_hash(user_in.password)
    
    # Prepare data for UserInDB, explicitly creating PyObjectId for id
    user_db_data = user_in.model_dump(exclude={"password"}) # Should be model_dump
    user_db_data["password_hash"] = hashed_password
    
    
    new_user_obj = UserInDB(**user_db_data) # This will generate _id via default_factory
    result = await user_collection.insert_one(new_user_obj.model_dump(by_alias=True))
    
    created_user_dict = await user_collection.find_one({"_id": result.inserted_id})
    if not created_user_dict:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create user.")

    created_user_instance = UserInDB(**created_user_dict)

    # Automatically log in the user by creating a session
    # Store user ID as string in session, as ObjectId is not directly JSON serializable for session cookie
    request.session["user_id"] = str(created_user_instance.id) 
    request.session["username"] = created_user_instance.username

    return to_user_out(created_user_instance)


@UserRouter.post("/login", response_model=UserOut)
async def login_for_session(form_data: UserLogin, request: Request):
    user_collection = get_user_collection()
    user_dict = await user_collection.find_one({"username": form_data.username})
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Session"},
        )
    user = UserInDB(**user_dict)
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Session"},
        )

    # Create session - store user ID as string
    request.session["user_id"] = str(user.id)
    request.session["username"] = user.username
    
    return to_user_out(user)

@UserRouter.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Successfully logged out"}

@UserRouter.get("/me", response_model=UserOut)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    return to_user_out(current_user)
