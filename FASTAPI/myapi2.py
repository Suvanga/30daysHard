
from fastapi import FastAPI, HTTPException, status, Path, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from pydantic import BaseModel
from typing import Optional, List   


app = FastAPI(title = "Simple Sql integration ")

#DATABASE SETUP 

engine = create_engine("sqlite:///users.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base =declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable = False)

Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    name: str
    email: str
    role:str

class UserResponse(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[str]
    role: Optional[str]


#getting the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

get_db()

#api setup 
@app.get("/")
def root():
    return {"message": "Welcome to the Simple SQL Integration API"}

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id:int, db:Session =Depends(get_db)):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

@app.post("/users/", response_model=User)
def create_user(user: User):
    db = SessionLocal()
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user
