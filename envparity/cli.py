"""Command-line interface for envparity."""

import argparse
import json
import os
import sys

from . import __version__
from .scanner import parse_env_file, scan_dir


def _resolve(root, p):
    if os.path.isabs(p):
        return p
    return os.path.join(root, p)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="envparity",
        description="Compare environment variables referenced in source code against a .env file.",
    )
    parser.add_argument("path", nargs="?", default=".", help="project root to scan (default: .)")
    parser.add_argument("--env-file", default=".env.example",
                        help="env file to compare against (default: .env.example)")
    parser.add_argument("--compare", default=None,
                        help="also compare against a second env file (e.g. .env)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="output format (default: text)")
    parser.add_argument("--fail", action="store_true",
                        help="exit with status 1 if any mismatch is found")
    parser.add_argument("--version", action="version", version="envparity " + __version__)
    args = parser.parse_args(argv)

    root = os.path.abspath(args.path)
    code_vars, files_scanned = scan_dir(root)
    env_path = _resolve(root, args.env_file)
    env_keys = parse_env_file(env_path)

    result = {
        "root": root,
        "files_scanned": files_scanned,
        "env_file": env_path,
        "code_vars": sorted(code_vars),
        "env_keys": sorted(env_keys),
        "missing_from_env": sorted(code_vars - env_keys),   # referenced in code, absent from env file
        "orphaned_in_env": sorted(env_keys - code_vars),     # in env file, never referenced
    }

    if args.compare:
        other_path = _resolve(root, args.compare)
        other_keys = parse_env_file(other_path)
        result["compare_file"] = other_path
        result["compare_keys"] = sorted(other_keys)
        result["missing_from_compare"] = sorted(code_vars - other_keys)
        result["only_in_env_file"] = sorted(env_keys - other_keys)
        result["only_in_compare"] = sorted(other_keys - env_keys)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print("envparity — {} ({} files scanned)".format(root, files_scanned))
        print("env file: {}".format(env_path))
        print("")
        print("Referenced in code ({}):".format(len(code_vars)))
        for v in sorted(code_vars):
            mark = "OK" if v in env_keys else "MISSING"
            print("  [{}] {}".format(mark, v))
        print("")
        print("In env file but never referenced ({}):".format(len(result["orphaned_in_env"])))
        for v in result["orphaned_in_env"]:
            print("  {}".format(v))
        if args.compare:
            print("")
            print("Compare file: {}".format(result["compare_file"]))
            print("  only in {}: {}".format(args.env_file, ", ".join(result["only_in_env_file"]) or "(none)"))
            print("  only in {}: {}".format(args.compare, ", ".join(result["only_in_compare"]) or "(none)"))

    has_issue = bool(result["missing_from_env"]) or bool(result["orphaned_in_env"])
    if args.compare:
        has_issue = has_issue or bool(result["only_in_env_file"]) or bool(result["only_in_compare"])
    if args.fail and has_issue:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())