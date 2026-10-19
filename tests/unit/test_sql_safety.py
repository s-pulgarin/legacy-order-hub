"""Guardia contra inyección SQL (RNF-02.2).

Analiza el código de la capa de persistencia y exige que toda llamada a
`execute()` / `executemany()` reciba el SQL como texto literal fijo. Así los
valores solo pueden llegar por parameter binding (`?`); un f-string, una
concatenación con variables, `.format()` o `%` hacen fallar la prueba.
"""

import ast
from pathlib import Path

import pytest

PERSISTENCE_DIR = (
    Path(__file__).resolve().parents[2]
    / "orderhub"
    / "adapters"
    / "outbound"
    / "persistence"
)
SQL_METHODS = {"execute", "executemany", "executescript"}


def _sql_calls(path: Path):
    """Devuelve (línea, primer argumento) de cada llamada SQL del archivo."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in SQL_METHODS
            and node.args
        ):
            yield node.lineno, node.args[0]


def _is_literal_sql(node: ast.AST) -> bool:
    """True solo para un literal de texto (las líneas contiguas se unen en uno)."""
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


PYTHON_FILES = sorted(PERSISTENCE_DIR.rglob("*.py"))


def test_hay_archivos_de_persistencia_para_revisar():
    names = {p.name for p in PYTHON_FILES}
    assert {
        "user_repository.py",
        "product_repository.py",
        "order_repository.py",
    } <= names


@pytest.mark.parametrize("path", PYTHON_FILES, ids=lambda p: p.name)
def test_todas_las_consultas_usan_sql_literal_con_parametros(path):
    unsafe = [
        f"{path.name}:{line} ({type(arg).__name__})"
        for line, arg in _sql_calls(path)
        if not _is_literal_sql(arg)
    ]
    assert unsafe == [], f"SQL construido dinámicamente: {unsafe}"


@pytest.mark.parametrize(
    "snippet",
    [
        "conn.execute(f\"SELECT * FROM users WHERE username = '{username}'\")",
        'conn.execute("SELECT * FROM users WHERE id = " + user_id)',
        'conn.execute("SELECT * FROM users WHERE id = {}".format(user_id))',
        'conn.execute("SELECT * FROM users WHERE id = %s" % user_id)',
        "conn.execute(query)",
    ],
)
def test_la_guardia_detecta_sql_dinamico(snippet, tmp_path):
    bad_file = tmp_path / "bad_repository.py"
    bad_file.write_text(snippet, encoding="utf-8")

    assert [arg for _, arg in _sql_calls(bad_file) if not _is_literal_sql(arg)]


def test_la_guardia_acepta_sql_parametrizado(tmp_path):
    good_file = tmp_path / "good_repository.py"
    good_file.write_text(
        'conn.execute("SELECT * FROM users WHERE username = ?", (username,))',
        encoding="utf-8",
    )

    assert all(_is_literal_sql(arg) for _, arg in _sql_calls(good_file))
