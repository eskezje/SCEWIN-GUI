from dataclasses import dataclass
from typing import List, Optional

@dataclass
class BIOSSetting:
    setup_question: str = ""
    help_string: str = ""
    token: str = ""
    offset: str = ""
    width: str = ""
    bios_default: Optional[str] = None
    options: List[str] = None
    active_option: Optional[int] = None
    value: Optional[str] = None
    content: List[str] = None

    @property
    def unique_id(self) -> str:
        """Create a unique identifier for this setting"""
        return f"{self.setup_question}||{self.token}||{self.offset}"
