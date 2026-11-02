"""Persist a private, unpredictable signing key outside the repository."""
import os
import secrets
from pathlib import Path

def local_secret(instance_path):
    supplied = os.environ.get("HELPDESK_SECRET_KEY")
    if supplied:
        if len(supplied) < 32:
            raise RuntimeError("HELPDESK_SECRET_KEY must have at least 32 characters")
        return supplied
    target = Path(instance_path) / ".session_secret"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(secrets.token_urlsafe(48))
    secret = target.read_text(encoding="utf-8").strip()
    if len(secret) < 32:
        raise RuntimeError("Signing key missing or invalid")
    return secret
