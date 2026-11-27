"""Guardrails in layers: screen untrusted text, redact personal data, check output, gate actions.

Pattern matching catches obvious injection only and is easy to evade. The control that holds is the
approval gate: no text, from a posting or a model, can approve an action.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets

INJECTION = {
    "override": r"\b(ignore|disregard|forget)\b.{0,40}\b(previous|prior|above|all)\b.{0,20}\b(instructions?|rules|prompts?)",
    "role change": r"\byou are now\b|\bsystem prompt\b|\bact as the system\b",
    "exfiltration": r"\b(send|email|post|upload)\b.{0,60}\b(resume|ssn|passport|password|api key|token)s?\b.{0,40}\b(to|at)\b",
    "applicant bot bait": r"\bif you are an? (ai|llm|language model|assistant)\b",
}
PII = {
    "email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "phone": r"(?<![\w])(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?![\w])",
}


def scan_injection(text: str) -> list[str]:
    return [name for name, pattern in INJECTION.items() if re.search(pattern, text, re.I | re.S)]


def redact(text: str) -> str:
    for label, pattern in PII.items():
        text = re.sub(pattern, f"[{label}]", text)
    return text


def fence(key: str, text: str) -> str:
    """Delimit untrusted text and stop it from closing its own delimiter."""
    return f'<passage id="{key}">{text.replace("<", "&lt;")}</passage>'


def check_citations(reply: str, allowed: set[str]) -> bool:
    cited = set(re.findall(r"\[([^\[\]]+#\d+)\]", reply))
    return bool(cited) and cited <= allowed


class ApprovalGate:
    """A token approves one action on one exact payload, once. Editing the draft voids it.

    `issue` belongs to the human-facing side. Never expose it to a model or an agent tool.
    """

    def __init__(self) -> None:
        self._key = secrets.token_bytes(32)
        self._used: set[str] = set()

    def issue(self, action: str, payload: str) -> str:
        return hmac.new(self._key, f"{action}\0{payload}".encode(), hashlib.sha256).hexdigest()

    def consume(self, token: str, action: str, payload: str) -> bool:
        if token in self._used or not hmac.compare_digest(token.encode(), self.issue(action, payload).encode()):
            return False
        self._used.add(token)
        return True
