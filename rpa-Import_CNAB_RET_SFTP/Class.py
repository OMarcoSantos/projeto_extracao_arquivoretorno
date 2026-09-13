from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Rerun:
    driver: str
    email: str
    senhaBanco: str
    link: str
    dfBase: Optional[Any] = None
