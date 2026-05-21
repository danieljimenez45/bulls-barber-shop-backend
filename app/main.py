import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.logging import RequestLoggingMiddleware, get_logger, setup_logging
from app.database import create_tables
from app.api.routers import admin, auth, bookings, contact, gallery, reviews, services

# Inicializar logging antes de cualquier otra importación que pueda loggear
setup_logging(debug=settings.DEBUG)
logger = get_logger(__name__)

app = FastAPI(
    title="Bulls Barber Shop API",
    description="API para la barbería Bulls Barber Shop 🐂",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Middleware — orden importa: primero logging, luego CORS ───────────────────
app.add_middleware(RequestLoggingMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["X-Total-Count"],
)

# ── Archivos estáticos (imágenes de galería) ──────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Rutas ─────────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(services.router, prefix="/api/services", tags=["Servicios"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Reservas"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reseñas"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["Galería"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contacto"])


# ── Eventos ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    create_tables()
    logger.info(
        "Bulls Barber Shop API arrancada",
        extra={"debug": settings.DEBUG, "cors_origins": settings.get_cors_origins()},
    )


# ── Endpoints básicos ─────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {"message": "Bulls Barber Shop API 🐂", "docs": "/docs"}


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "ok"}
