"""
Script de un solo uso para crear el usuario administrador de Bulls Barber Shop.

Uso:
    cd backend
    python -m scripts.create_admin

Se puede ejecutar de nuevo para cambiar la contraseña: si el email ya existe,
actualiza la contraseña y reactiva la cuenta.
"""

import sys
import os

# Asegura que el paquete `app` sea localizable desde la raíz del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from getpass import getpass

from app.database import SessionLocal, create_tables
from app.domain.auth.entity import AdminUser
from app.infrastructure.persistence.orm.user import UserORM
from app.infrastructure.security.password_hasher import BcryptPasswordHasher


def main() -> None:
    print("═" * 50)
    print("  Bulls Barber Shop — Crear / Actualizar Admin")
    print("═" * 50)

    email = input("Email del admin: ").strip().lower()
    if not email:
        print("❌ El email no puede estar vacío.")
        sys.exit(1)

    password = getpass("Contraseña: ")
    if len(password) < 8:
        print("❌ La contraseña debe tener al menos 8 caracteres.")
        sys.exit(1)

    confirm = getpass("Confirma la contraseña: ")
    if password != confirm:
        print("❌ Las contraseñas no coinciden.")
        sys.exit(1)

    # Crear tablas si aún no existen (primera ejecución)
    create_tables()

    hasher = BcryptPasswordHasher()
    hashed = hasher.hash(password)

    db = SessionLocal()
    try:
        existing = db.query(UserORM).filter(UserORM.email == email).first()
        if existing:
            existing.hashed_password = hashed
            existing.is_active = True
            db.commit()
            print(f"\n✅ Contraseña actualizada para: {email}")
        else:
            user = UserORM(email=email, hashed_password=hashed, is_active=True)
            db.add(user)
            db.commit()
            print(f"\n✅ Admin creado correctamente: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
