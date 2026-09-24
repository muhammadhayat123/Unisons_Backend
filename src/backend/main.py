from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Database and Models import (Tables banane ke liye)
# Note: Apne actual database/models path ke mutabiq check kar lein
try:
    from src.backend.database import engine, Base
    # Saare models import karein taake tables register ho sakein
    import src.backend.models 
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Table creation note: {e}")

from src.backend.routes.user_route import user_route
from src.backend.routes.company_route import company_route
from src.backend.routes.customer_route import customer_route
from src.backend.routes.inquiry_route import inquiry_route
from src.backend.routes.admin_route import admin_route
from src.backend.routes.seller_route import seller_route
from src.backend.routes.websocket_route import ws_route
from src.backend.routes.tracking_route import tracking_route, admin_tracking_route, ws_tracking_route

app = FastAPI(title="Inquiry Management API", version="2.0.0")

# Allowed origins me Vercel ka domain lazmi add karein
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "https://unisons-signup.vercel.app",  # Aapka Vercel domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Saare Vercel preview domains ke liye
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth (existing)
app.include_router(user_route, prefix="/user", tags=["user"])

# Existing routes
app.include_router(company_route)
app.include_router(customer_route)
app.include_router(inquiry_route)
app.include_router(admin_route)
app.include_router(seller_route)
app.include_router(ws_route)

# Seller Location Tracking (additive)
app.include_router(tracking_route)
app.include_router(admin_tracking_route)
app.include_router(ws_tracking_route)