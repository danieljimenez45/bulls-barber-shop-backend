# Bulls Barber Shop — Backend

API REST construida con **FastAPI** + **SQLAlchemy** + **SQLite** (dev) / **PostgreSQL** (prod).

## Requisitos

- Python 3.11+
- pip

## Instalación

```bash
# Clonar el repo y entrar en la carpeta
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt

# Crear el archivo .env a partir del ejemplo
cp .env.example .env
```

## Arrancar el servidor

```bash
uvicorn app.main:app --reload
```

La API estará en `http://localhost:8000`
Documentación interactiva en `http://localhost:8000/docs`

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/services` | Listar servicios |
| POST | `/api/bookings` | Crear reserva |
| GET | `/api/reviews` | Listar reseñas visibles |
| POST | `/api/reviews` | Enviar reseña |
| GET | `/api/gallery` | Listar fotos de galería |
| POST | `/api/contact` | Enviar mensaje de contacto |

## Estructura

```
backend/
├── app/
│   ├── main.py          # Punto de entrada FastAPI
│   ├── config.py        # Variables de entorno
│   ├── database.py      # SQLAlchemy setup
│   ├── models/          # Tablas de la BD
│   ├── schemas/         # Validación Pydantic
│   └── routers/         # Rutas de la API
├── requirements.txt
└── .env.example
```
