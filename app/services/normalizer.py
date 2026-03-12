from app.parsers.registry import registry

def infer_event_type(data: dict) -> str:
    if data.get("event_type"):
        return str(data["event_type"])
    msg = str(data.get("message", "")).lower()
    action = str(data.get("action", "")).lower()
    source = str(data.get("source", "")).lower()
    process = str(data.get("process_name", "")).lower()

    if "powershell" in process or "powershell" in msg:
        return "process_start"
    if "fail" in action or "authentication failure" in msg:
        return "authentication_failure"
    if "success" in action or "authentication success" in msg:
        return "authentication_success"
    if source in {"firewall", "proxy"} or data.get("dst_ip"):
        return "network_connection"
    return "generic_event"

def infer_severity(data: dict) -> str:
    sev = str(data.get("severity", "")).lower()
    if sev in {"critical", "high", "medium", "low", "info"}:
        return sev
    if data.get("ioc_match"):
        return "high"
    return "info"

def normalize_line(text: str, file_name: str = "") -> dict:
    parsed = registry.parse_line(text, file_name)
    if not parsed:
        return {
            "source": "unknown",
            "event_type": "generic_event",
            "message": text,
            "parse_status": "failed",
            "parse_confidence": 0.0,
            "parser_name": "none",
            "detected_format": "unknown",
            "severity": "info",
        }

    data = dict(parsed.data)
    data.setdefault("source", file_name.rsplit(".", 1)[0] if file_name else "unknown")
    data["event_type"] = infer_event_type(data)
    data["severity"] = infer_severity(data)
    data["parse_status"] = parsed.status
    data["parse_confidence"] = parsed.confidence
    data["parser_name"] = parsed.parser_name
    data["detected_format"] = parsed.detected_format

    if data.get("dst_port"):
        try:
            data["dst_port"] = int(str(data["dst_port"]))
        except Exception:
            data["dst_port"] = None

    return data
