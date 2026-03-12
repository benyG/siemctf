from app.parsers.json_line import JsonLineParser
from app.parsers.key_value import KeyValueParser
from app.parsers.regex_fallback import RegexFallbackParser

class ParserRegistry:
    def __init__(self):
        self.parsers = [JsonLineParser(), KeyValueParser(), RegexFallbackParser()]

    def parse_line(self, text: str, file_name: str = ""):
        best = None
        best_score = -1
        for parser in self.parsers:
            score = parser.can_parse(text, file_name)
            if score > best_score:
                result = parser.parse(text, file_name)
                if result:
                    best = result
                    best_score = score
        return best

registry = ParserRegistry()
