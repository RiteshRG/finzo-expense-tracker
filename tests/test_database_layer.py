from pathlib import Path


def test_database_module_uses_direct_pymysql_pattern():
    source = Path("database/__init__.py").read_text(encoding="utf-8")

    assert "sqlalchemy" not in source.lower()
    assert "pymysql" in source.lower()
    assert "get_connection" in source
    assert "init_db" in source
    assert "seed_db" in source
