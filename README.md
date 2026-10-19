# envparity

Compare environment variables referenced in your source code against your `.env` / `.env.example` files, so undocumented or orphaned configuration never ships.

## Features

- Scans a project tree for environment variable references across JavaScript/TypeScript, Python, Go, Rust, and shell templates.
- Recognizes `process.env.X`, `process.env["X"]`, `os.environ["X"]`, `os.getenv("X")`, `os.Getenv("X")`, `env!("X")`, `env_var("X")`, and `${X}`.
- Parses `.env`-style files (comments, `export`, quoted keys).
- Reports variables referenced in code but missing from the env file, and keys present in the env file but never referenced.
- Optional second-file comparison (e.g. `.env` vs `.env.example`).
- Text and JSON output; non-zero exit code on `--fail`.

## Install

```bash
pip install -e .
```

Or run directly:

```bash
python -m envparity.cli .
```

## Usage

```bash
# Basic scan against .env.example
envparity .

# Use a different env file
envparity . --env-file .env

# Compare .env.example against .env
envparity . --env-file .env.example --compare .env

# JSON output for CI
envparity . --format json

# Fail the build on mismatches
envparity . --fail
```

Example output:

```
envparity — /path/to/project (42 files scanned)
env file: /path/to/project/.env.example

Referenced in code (3):
  [OK]      API_KEY
  [MISSING] DB_URL
  [OK]      PORT

In env file but never referenced (1):
  GAMMA
```

## License

MIT