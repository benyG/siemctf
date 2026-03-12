import re
import shlex
from sqlalchemy import and_, or_, not_, String, Text, cast

ALLOWED_FIELDS = {
    "id", "timestamp", "source", "event_type", "hostname", "username",
    "src_ip", "dst_ip", "dst_port", "process_name", "command_line",
    "action", "severity", "message", "parse_status", "ioc_match", "parser_name"
}

DEFAULT_TEXT_FIELDS = ["message", "command_line", "process_name", "hostname", "username", "src_ip", "dst_ip", "ioc_match"]

OPS = (">=", "<=", ">", "<", "~", ":")

def _prepare_query(q: str) -> str:
    q = (q or "").strip()
    q = q.replace("(", " ( ").replace(")", " ) ")
    return q

def tokenize_query(q: str) -> list[str]:
    if not q:
        return []
    prepared = _prepare_query(q)
    return shlex.split(prepared)

def _make_clause(model, field: str, op: str, value: str):
    col = getattr(model, field)
    if op == ":":
        if "*" in value:
            like = value.replace("*", "%")
            return col.ilike(like)
        return col == value
    if op == "~":
        return cast(col, String).ilike(f"%{value}%")
    if op == ">=":
        return cast(col, String) >= value
    if op == "<=":
        return cast(col, String) <= value
    if op == ">":
        return cast(col, String) > value
    if op == "<":
        return cast(col, String) < value
    raise ValueError(f"Unsupported operator: {op}")

def parse_atom(token: str) -> tuple[str, str, str] | None:
    for op in OPS:
        if op in token:
            field, value = token.split(op, 1)
            field = field.strip()
            value = value.strip()
            if field in ALLOWED_FIELDS and value:
                return field, op, value
    return None

def build_free_text_clause(model, term: str):
    like = f"%{term}%"
    clauses = [cast(getattr(model, field), String).ilike(like) for field in DEFAULT_TEXT_FIELDS]
    return or_(*clauses)

def to_rpn(tokens: list[str]) -> list[str]:
    precedence = {"OR": 1, "AND": 2, "NOT": 3}
    output = []
    stack = []

    prev_was_operand = False
    normalized = []
    for token in tokens:
        upper = token.upper()
        is_operand = upper not in {"AND", "OR", "NOT", "(", ")"}
        if prev_was_operand and (is_operand or upper in {"NOT", "("}):
            normalized.append("AND")
        normalized.append(token)
        prev_was_operand = is_operand or token == ")"

    for token in normalized:
        upper = token.upper()
        if token == "(":
            stack.append(token)
        elif token == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if stack and stack[-1] == "(":
                stack.pop()
        elif upper in precedence:
            while stack and stack[-1] != "(" and precedence.get(stack[-1], 0) >= precedence[upper]:
                output.append(stack.pop())
            stack.append(upper)
        else:
            output.append(token)

    while stack:
        output.append(stack.pop())
    return output

def build_condition(model, q: str):
    tokens = tokenize_query(q)
    if not tokens:
        return None

    rpn = to_rpn(tokens)
    stack = []

    for token in rpn:
        upper = token.upper()
        if upper == "NOT":
            if not stack:
                continue
            stack.append(not_(stack.pop()))
            continue
        if upper in {"AND", "OR"}:
            if len(stack) < 2:
                continue
            b = stack.pop()
            a = stack.pop()
            stack.append(and_(a, b) if upper == "AND" else or_(a, b))
            continue

        atom = parse_atom(token)
        if atom:
            field, op, value = atom
            stack.append(_make_clause(model, field, op, value))
        else:
            stack.append(build_free_text_clause(model, token))

    return stack[-1] if stack else None

def parse_query_string(q: str) -> dict:
    return {
        "raw": q or "",
        "tokens": tokenize_query(q),
        "mode": "pseudo-kql-spl"
    }

def query_help_examples() -> list[str]:
    return [
        'source:sysmon AND process_name:powershell.exe',
        'hostname:HR-LT-17 AND "encodedcommand"',
        'source:firewall AND dst_ip:45.77.*',
        'username:jdupont AND NOT severity:info',
        'message~phishing OR command_line~base64'
    ]
