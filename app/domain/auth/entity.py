from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AdminUser:
    email: str
    hashed_password: str
    id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
