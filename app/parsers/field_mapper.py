ALIASES = {
    "timestamp": ["timestamp", "time", "@timestamp", "date"],
    "source": ["source", "channel"],
    "hostname": ["host", "hostname", "computer", "device"],
    "username": ["user", "username", "account", "login"],
    "src_ip": ["src", "src_ip", "source_ip", "client_ip"],
    "dst_ip": ["dst", "dst_ip", "dest_ip", "destination_ip"],
    "dst_port": ["dst_port", "dport", "port", "destination_port"],
    "process_name": ["process", "process_name", "image"],
    "command_line": ["command_line", "cmd", "command"],
    "action": ["action", "status", "result"],
    "message": ["message", "msg", "description"],
    "severity": ["severity", "level"],
    "event_type": ["event_type", "type"],
}

def map_fields(data: dict) -> dict:
    lowered = {str(k).lower(): v for k, v in data.items()}
    out = {}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            if alias in lowered:
                out[target] = lowered[alias]
                break
    return out
