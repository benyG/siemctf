from dataclasses import dataclass, field
from typing import Any

@dataclass
class ParseResult:
    data: dict[str, Any]
    confidence: float
    status: str = "parsed"
    parser_name: str = "base"
    detected_format: str = "unknown"
    warnings: list[str] = field(default_factory=list)

class BaseParser:
    name = "base"

    def can_parse(self, text: str, file_name: str = "") -> float:
        return 0.0

    def parse(self, text: str, file_name: str = "") -> ParseResult | None:
        return None
