"""
test_no_legacy.py — Guardia CI contra la reaparición de carpetas legacy.

Las carpetas app/routers/, app/models/ y app/schemas/ fueron eliminadas porque
contenían código sin autenticación que podría re-montarse accidentalmente en
main.py y exponer operaciones sensibles sin JWT.

Este test falla inmediatamente si alguna de esas carpetas reaparece con código
Python, actuando como recordatorio de que NO deben volver al proyecto.
"""

import os
from pathlib import Path

import pytest

# Raíz del paquete app (dos niveles arriba de este fichero)
APP_ROOT = Path(__file__).parent.parent / "app"

LEGACY_PATHS = [
    APP_ROOT / "routers",
    APP_ROOT / "models",
    APP_ROOT / "schemas",
]


@pytest.mark.unit
def test_carpetas_legacy_no_existen():
    """Las carpetas legacy no deben existir en el árbol de la aplicación."""
    encontradas = [
        str(p.relative_to(APP_ROOT.parent))
        for p in LEGACY_PATHS
        if p.exists() and any(p.glob("*.py"))
    ]
    assert not encontradas, (
        "Se han detectado carpetas legacy con código Python. "
        "Estas carpetas no deben estar en el proyecto:\n"
        + "\n".join(f"  • {p}" for p in encontradas)
        + "\n\nSi necesitas añadir funcionalidad, usa app/api/routers/ (con JWT)."
    )
