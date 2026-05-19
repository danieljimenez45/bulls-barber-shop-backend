import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import create_tables
from app.routers import bookings, contact, gallery, reviews, services

app = FastAPI(
    title="Bulls Barber Shop API",
    description="API para la barbería Bulls Barber Shop 🐂",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Archivos estáticos (imágenes de galería) ──────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Rutas ─────────────────────────────────────────────────────────────────────
app.include_router(services.router, prefix="/api/services", tags=["Servicios"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Reservas"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reseñas"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["Galería"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contacto"])


# ── Eventos ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    create_tables()


# ── Endpoints básicos ─────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {"message": "Bulls Barber Shop API 🐂", "docs": "/docs"}


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "ok"}
