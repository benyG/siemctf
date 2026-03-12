import re
from app.parsers.base import BaseParser, ParseResult

TS = re.compile(r'(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}Z?)')
IP = re.compile(r'(?P<ip>(?:\d{1,3}\.){3}\d{1,3})')
HOST = re.compile(r'(?:host|hostname|computer)[:=](?P<hostname>[\w.-]+)', re.I)
USER = re.compile(r'(?:user|username|account)[:=](?P<username>[\w.-]+)', re.I)

class RegexFallbackParser(BaseParser):
    name = "regex_fallback"

    def can_parse(self, text: str, file_name: str = "") -> float:
        if TS.search(text) or IP.search(text):
            return 0.35
        return 0.1

    def parse(self, text: str, file_name: str = "") -> ParseResult | None:
        data = {"message": text}
        ts = TS.search(text)
        if ts:
            data["timestamp"] = ts.group("timestamp").replace(" ", "T")
        host = HOST.search(text)
        if host:
            data["hostname"] = host.group("hostname")
        user = USER.search(text)
        if user:
            data["username"] = user.group("username")
        ips = [m.group("ip") for m in IP.finditer(text)]
        if ips:
            data["src_ip"] = ips[0]
        if len(ips) > 1:
            data["dst_ip"] = ips[1]
        low = text.lower()
        if "powershell" in low:
            data["process_name"] = "powershell.exe"
            data["event_type"] = "process_start"
        elif "auth" in low and "fail" in low:
            data["event_type"] = "authentication_failure"
        elif "auth" in low and "success" in low:
            data["event_type"] = "authentication_success"
        if "sysmon" in file_name.lower():
            data["source"] = "sysmon"
        elif "firewall" in file_name.lower():
            data["source"] = "firewall"
        elif "vpn" in file_name.lower():
            data["source"] = "vpn"
        return ParseResult(data=data, confidence=0.40 if len(data) >= 3 else 0.20, status="partial", parser_name=self.name, detected_format="regex")
