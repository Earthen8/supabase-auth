import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client, AuthApiError

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL:
    SUPABASE_URL = SUPABASE_URL.replace("/rest/v1", "").rstrip("/")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL dan SUPABASE_KEY harus diisi di .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Auth API - Supabase & FastAPI",
    description="Otonomy API and Route Protection Using Supabase Auth",
    version="1.0.0"
)

security = HTTPBearer()

class AuthSchema(BaseModel):
    email: EmailStr
    password: str

# Middleware / Dependency untuk verifikasi JWT Token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(jwt=token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user_response.user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"}
        )

# Stage 1: Auth Routes
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(data: AuthSchema):
    try:
        response = supabase.auth.sign_up({"email": data.email, "password": data.password})
        if not response.user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "Sign up failed"})
        return response.user
    except AuthApiError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": e.message})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": str(e)})

@app.post("/auth/login")
def login(data: AuthSchema):
    try:
        response = supabase.auth.sign_in_with_password({"email": data.email, "password": data.password})
        if not response.session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "Invalid login credentials"})
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer"
        }
    except AuthApiError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": e.message})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "Invalid login credentials"})

# Stage 4: Logout Route
@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user=Depends(get_current_user), credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        supabase.auth.admin.sign_out(credentials.credentials)
    except Exception:
        pass
    return None

# Stage 2: Public Route
@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

# Stage 3 & 4: Protected Route
@app.get("/protected/profile")
def protected_profile(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }