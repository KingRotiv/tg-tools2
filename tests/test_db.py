import tempfile
from pathlib import Path

import pytest

from tg_tools.db import DBManager


@pytest.fixture
def temp_db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_db.json"
        yield str(db_path)


def test_set_and_get_config(temp_db_path):
    """
    Testa se é possível salvar uma configuração e recuperá-la corretamente.
    """
    db = DBManager(temp_db_path)
    db.set_config("chave", "valor")
    assert db.get_config("chave") == "valor"


def test_get_config_default(temp_db_path):
    """
    Testa se retorna o valor padrão quando a chave não existe no banco.
    """
    db = DBManager(temp_db_path)
    assert db.get_config("inexistente", default="padrao") == "padrao"


def test_remove_config(temp_db_path):
    """
    Testa se uma configuração pode ser removida corretamente.
    """
    db = DBManager(temp_db_path)
    db.set_config("chave", "valor")
    db.remove_config("chave")
    assert db.get_config("chave") is None


def test_clear_configs(temp_db_path):
    """
    Testa se todas as configurações podem ser limpas do banco.
    """
    db = DBManager(temp_db_path)
    db.set_config("a", "1")
    db.set_config("b", "2")
    db.clear_configs()
    assert db.get_config("a") is None
    assert db.get_config("b") is None
