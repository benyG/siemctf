import shlex
from app.parsers.base import BaseParser, ParseResult
from app.parsers.field_mapper import map_fields

class KeyValueParser(BaseParser):
    name = "key_value"

    def can_parse(self, text: str, file_name: str = "") -> float:
        count = text.count("=")
        if count >= 4:
            return 0.92
        if count >= 2:
            return 0.65
        return 0.0

    def parse(self, text: str, file_name: str = "") -> ParseResult | None:
        try:
            tokens = shlex.split(text)
        except ValueError:
            tokens = text.split()
        raw = {}
        for token in tokens:
            if "=" in token:
                k, v = token.split("=", 1)
                raw[k] = v
        if not raw:
            return None
        data = map_fields(raw)
        data.setdefault("message", text)
        status = "parsed" if len(raw) >= 4 else "partial"
        confidence = 0.92 if status == "parsed" else 0.65
        return ParseResult(data=data, confidence=confidence, status=status, parser_name=self.name, detected_format="kv")
