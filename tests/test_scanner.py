import os
import tempfile

from envparity.scanner import extract_vars, parse_env_file, scan_dir


def test_extract_vars_js():
    text = "const x = process.env.API_KEY; const y = process.env['DB_URL']; const z = process.env[\"SECRET\"]"
    assert extract_vars(text) == {"API_KEY", "DB_URL", "SECRET"}


def test_extract_vars_python():
    text = 'import os\na = os.environ["FOO"]\nb = os.getenv("BAR")\nc = os.getenv(\'BAZ\', "d")'
    assert extract_vars(text) == {"FOO", "BAR", "BAZ"}


def test_parse_env_file():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, ".env.example")
        with open(p, "w") as f:
            f.write("# comment\nAPI_KEY=secret\nDB_URL=\nexport PORT=3000\n")
        assert parse_env_file(p) == {"API_KEY", "DB_URL", "PORT"}


def test_scan_dir():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "app.py"), "w") as f:
            f.write('x = os.getenv("ALPHA")\ny = os.environ["BETA"]')
        with open(os.path.join(d, ".env.example"), "w") as f:
            f.write("ALPHA=1\nGAMMA=2\n")
        vars_found, n = scan_dir(d)
        assert vars_found == {"ALPHA", "BETA"}
        assert n >= 2