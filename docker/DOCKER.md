# Docker — Bulls Barber Shop API

Guía para levantar el backend en contenedor Docker, tanto en desarrollo como en producción.

---

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Fichero `.env` creado en la raíz del repo (`backend/.env`)

```bash
cp .env.example .env
# Abre .env y rellena los valores (SECRET_KEY, SMTP, Cloudinary, etc.)
```

---

## Estructura de ficheros

```
backend/
├── docker/
│   ├── Dockerfile                 # stages: base → dev / prod
│   ├── docker-compose.dev.yml     # entorno de desarrollo
│   ├── docker-compose.prod.yml    # entorno de producción
│   └── DOCKER.md                  # esta guía
├── .dockerignore
└── .env.example
```

---

## Desarrollo

El contenedor monta el código fuente como volumen. Cualquier cambio que hagas en los ficheros Python se refleja automáticamente gracias a `--reload` de uvicorn, **sin necesidad de reconstruir la imagen**.

### Levantar

```bash
# Desde la raíz del repo backend/
docker compose -f docker/docker-compose.dev.yml up --build
```

La API queda disponible en **http://localhost:8000**  
Documentación interactiva: **http://localhost:8000/docs**

### Parar

```bash
docker compose -f docker/docker-compose.dev.yml down
```

### Ver logs

```bash
docker compose -f docker/docker-compose.dev.yml logs -f
```

### Abrir una terminal dentro del contenedor

```bash
docker compose -f docker/docker-compose.dev.yml exec backend bash
```

---

## Producción

La imagen se construye copiando el código dentro del contenedor. No hay volúmenes de código ni `--reload`. El proceso corre con un usuario sin privilegios por seguridad.

### Primera vez — preparar el entorno

```bash
# 1. Asegúrate de que .env tiene los valores de producción
#    (SECRET_KEY segura, DEBUG=false, SMTP real, Cloudinary, etc.)

# 2. Construir y levantar en segundo plano
docker compose -f docker/docker-compose.prod.yml up --build -d
```

### Primera vez — base de datos existente

Si ya tienes una base de datos creada antes de añadir Alembic (migraciones), márcala como ya migrada para que no intente re-crear las tablas:

```bash
docker compose -f docker/docker-compose.prod.yml exec backend alembic stamp 0001
```

Si la base de datos es nueva, Alembic la crea automáticamente al arrancar. No hace falta hacer nada.

### Levantar (arranques posteriores)

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

### Parar

```bash
docker compose -f docker/docker-compose.prod.yml down
```

### Ver logs

```bash
docker compose -f docker/docker-compose.prod.yml logs -f
```

### Reconstruir la imagen (tras actualizar código o dependencias)

```bash
docker compose -f docker/docker-compose.prod.yml up --build -d
```

### Abrir una terminal dentro del contenedor

```bash
docker compose -f docker/docker-compose.prod.yml exec backend bash
```

---

## Migraciones de base de datos

Las migraciones se aplican automáticamente al arrancar el contenedor (`alembic upgrade head`). Para gestionarlas manualmente:

```bash
# Ver el estado actual de las migraciones
docker compose -f docker/docker-compose.prod.yml exec backend alembic current

# Aplicar migraciones pendientes manualmente
docker compose -f docker/docker-compose.prod.yml exec backend alembic upgrade head

# Crear una nueva migración (tras modificar un modelo ORM)
docker compose -f docker/docker-compose.prod.yml exec backend alembic revision --autogenerate -m "descripcion_del_cambio"

# Revertir la última migración
docker compose -f docker/docker-compose.prod.yml exec backend alembic downgrade -1
```

---

## Volúmenes

| Volumen         | Ruta en el contenedor | Descripción                                      |
|-----------------|-----------------------|--------------------------------------------------|
| `uploads_data`  | `/app/uploads`        | Imágenes de galería subidas localmente           |

> Si usas **Cloudinary** como almacenamiento, este volumen queda vacío pero no interfiere.

Para inspeccionar o hacer backup del volumen:

```bash
# Ver dónde está montado en el host
docker volume inspect bulls_backend_uploads_data

# Backup del volumen a un fichero tar
docker run --rm \
  -v bulls_backend_uploads_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/uploads_backup.tar.gz -C /data .
```

---

## Puertos

| Servicio | Puerto host | Puerto contenedor |
|----------|-------------|-------------------|
| API      | 8000        | 8000              |

Para cambiar el puerto del host edita `docker-compose.prod.yml`:
```yaml
ports:
  - "8080:8000"   # ahora la API responde en localhost:8080
```

---

## Variables de entorno relevantes

| Variable                | Descripción                                         | Obligatoria en prod |
|-------------------------|-----------------------------------------------------|---------------------|
| `SECRET_KEY`            | Clave JWT — debe ser aleatoria y larga              | ✅                  |
| `DEBUG`                 | `false` en producción (desactiva /docs)             | ✅                  |
| `DATABASE_URL`          | URL de la base de datos                             | ✅                  |
| `CLOUDINARY_CLOUD_NAME` | Credenciales Cloudinary para galería                | Recomendada         |
| `CLOUDINARY_API_KEY`    |                                                     | Recomendada         |
| `CLOUDINARY_API_SECRET` |                                                     | Recomendada         |
| `SMTP_HOST`             | Servidor SMTP para notificaciones de reservas       | Recomendada         |

Consulta `.env.example` para la lista completa.
