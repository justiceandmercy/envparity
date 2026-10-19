"""Scanning helpers for envparity."""

import os
import re

# Patterns that capture an environment variable name from source code.
ENV_PATTERNS = [
    # JavaScript / TypeScript: process.env.FOO, process.env["FOO"], process.env['FOO']
    re.compile(r"process\.env(?:\.([A-Za-z_][A-Za-z0-9_]*)|\[\"([A-Za-z_][A-Za-z0-9_]*)\"\]|\['([A-Za-z_][A-Za-z0-9_]*)'\])"),
    # Python: os.environ["FOO"], os.environ['FOO'], os.getenv("FOO"), os.getenv('FOO', ...)
    re.compile(r"os\.environ\[[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']\]"),
    re.compile(r"os\.getenv\([\"']([A-Za-z_][A-Za-z0-9_]*)[\"']"),
    # Go: os.Getenv("FOO")
    re.compile(r"os\.Getenv\(\"([A-Za-z_][A-Za-z0-9_]*)\"\)"),
    # Rust: env!("FOO"), env_var("FOO")
    re.compile(r'env!\("([A-Za-z_][A-Za-z0-9_]*)"\)'),
    re.compile(r'env_var\("([A-Za-z_][A-Za-z0-9_]*)"\)'),
    # Shell / dotenv interpolation: ${FOO}
    re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}"),
]

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", ".cache", ".tox", "target",
    ".idea", ".vscode",
}

TEXT_EXTENSIONS = None  # None => try all files, skip binary


def extract_vars(text):
    """Return a set of environment variable names found in ``text``."""
    found = set()
    for pat in ENV_PATTERNS:
        for m in pat.finditer(text):
            for group in m.groups():
                if group:
                    found.add(group)
    return found


def scan_dir(root):
    """Walk ``root`` and return (set of var names, number of files scanned)."""
    vars_found = set()
    files_scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for fn in sorted(filenames):
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except OSError:
                continue
            if "\x00" in content[:4096]:
                continue
            v = extract_vars(content)
            if v:
                vars_found |= v
            files_scanned += 1
    return vars_found, files_scanned


def parse_env_file(path):
    """Return a set of keys defined in a .env-style file."""
    keys = set()
    if not os.path.exists(path):
        return keys
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export "):].strip()
                if "=" not in line:
                    continue
                key = line.split("=", 1)[0].strip()
                # strip optional quoting
                key = key.strip("\"'")
                if key and not key.startswith("#") and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
                    keys.add(key)
    except OSError:
        pass
    return keys