import json
from app.parsers.base import BaseParser, ParseResult
from app.parsers.field_mapper import map_fields

class JsonLineParser(BaseParser):
    name = "json_line"

    def can_parse(self, text: str, file_name: str = "") -> float:
        text = text.strip()
        return 0.98 if text.startswith("{") and text.endswith("}") else 0.0

    def parse(self, text: str, file_name: str = "") -> ParseResult | None:
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
        data = map_fields(obj)
        data.setdefault("message", text)
        return ParseResult(data=data, confidence=0.98, parser_name=self.name, detected_format="json")
