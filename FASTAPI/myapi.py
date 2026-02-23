#CRUD

#HTTP REQUESTS USING FASTAPI


from fastapi import FastAPI, HTTPException, status, Path
from typing import Optional
from pydantic import BaseModel

app = FastAPI()

users ={
1:{    
    "name":"Suvanga",
    "website": "https://suvanga.github.io/profile",
    "age": 24,
    "role": "Developer"
}
}



#base pydantic model

class User(BaseModel):
    name: str
    website: str
    age: int
    role: str

class UpdateUser(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    age: Optional[int] = None
    role: Optional[str] = None

class Config:
    orm_mode = True


@app.get("/")
def root():
    return {"Hello": "World"}


#Get users
@app.get("/users/{user_id}")
def get_user(user_id: int= Path(..., description="The ID of the user to retrieve"), gt=0, lt=100):
    if user_id not in users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return users[user_id] 

@app.post("/users/{user_id}", status_code=status.HTTP_201_CREATED)
def create_user(user_id: int, user: User):
    if user_id in users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    users[user_id] = user.dict()
    return user

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UpdateUser):
    if user_id not in users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    current_user = users[user_id]
    if user.name is not None:
        current_user["name"] = user.name
    if user.website is not None:
        current_user["website"] = user.website
    if user.age is not None:
        current_user["age"] = user.age
    if user.role is not None:
        current_user["role"] = user.role
    return current_user

@app.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int):
    if user_id not in users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    deleted_user = users.pop(user_id)
    return {"message": "User deleted successfully","deleted_info": deleted_user}


@app.get("/users/search")
def search_users(name: Optional[str] = None):
    if not name:
        return {"message": "Please provide a name to search for."}
    for user in users.values():
        if user["name"] == name:
            return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")