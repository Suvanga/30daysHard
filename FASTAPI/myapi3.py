#Building a secure FASTAPI with JWT python token authentication :)
from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base # Updated import path
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, List
from jose import JWTError, jwt

##FOR SECURITY AND JWT 
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

#security configuration: 
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") #responsible for password hashing
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") #Token we get from the user





app = FastAPI(title="Simple Sql integration API with Authentication", version="1.0")

# DATABASE SETUP 
engine = create_engine("sqlite:///users_Auth0.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# DATABASE MODEL
class User(Base):
    __tablename__ = "users_Auth0"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False) # FIX 1: Added missing column
    hashed_pwd = Column(String, nullable=False) # For storing hashed password
    is_active = Column(Boolean, default=True) # For soft deletion


Base.metadata.create_all(bind=engine)

# PYDANTIC MODELS
class UserCreate(BaseModel):
    name: str
    email: str
    role: str
    hashed_pwd: str

class UserResponse(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[str]
    role: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True


#For Authentication 
class UserAuth(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional [str] =None




##Helper functions
def verify_pwd(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_pwd_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return TokenData(email=email)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")










# GETTING THE DATABASE SESSION
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#Auh dependencies 
def get_current_user(token:str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    token_data = verify_token(token)
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
def get_current_active_user(current_user : User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# get_db()
















# API SETUP 
@app.get("/")
def root():
    return {"message": "Welcome to the Simple SQL Integration API And Authentication"}

@app.get("/profile", response_model = UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user:User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate,current_user:User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    
    hashed_password = get_pwd_hash(user.password)
    new_user = User(
        name = user.name,
        email = user.email,
        role = user.role,
        hashed_pwd = hashed_password
    )    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, update_user: UserCreate,current_user:User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    existing_user.name = update_user.name
    existing_user.email = update_user.email
    existing_user.role = update_user.role

    db.commit()
    db.refresh(existing_user)
    return existing_user

@app.delete("/deleteusers/{user_id}")
def delete_user(user_id:int, current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")
    db.delete(existing_user)
    db.commit()
    return {"message":"User deleted successfully"}

@app.get("/users/", response_model=list[UserResponse])
def get_users(current_user: User= Depends(get_current_active_user), db: Session = Depends(get_db)):
    return  db.query(User).all()
    



#Authentication endpoints
@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    hashed_password = get_pwd_hash(user.hashed_pwd)
    db_user = User(name = user.name, email=user.email, role=user.role, hashed_pwd=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_pwd(form_data.password, user.hashed_pwd):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}



@app.get("/verify-token")
def verify_token_endpoint(current_user: User= Depends(get_current_active_user)):
    return{
        "valid": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role
        }
    }

