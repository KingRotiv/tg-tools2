import os
from pathlib import Path

from tinydb import Query, TinyDB


class DBManager:
    def __init__(self, db_file: str = "config.json") -> None:
        # Cria o banco de dados no usuário
        data_dir = Path(os.path.expanduser("~"), ".tg-tools")
        data_dir.mkdir(exist_ok=True)
        self.db_full_path = Path(data_dir, db_file)
        self.db = TinyDB(self.db_full_path)
        self.config_table = self.db.table("config")

    def set_config(self, key: str, value: str) -> None:
        # Insere ou atualiza uma configuração
        self.config_table.upsert({"key": key, "value": value}, Query().key == key)

    def get_config(self, key: str, default: str | None = None) -> str | None:
        # Recupera uma configuração ou retorna um valor padrão
        result = self.config_table.get(Query().key == key)
        return result["value"] if result else default  # type: ignore

    def remove_config(self, key: str) -> None:
        # Remove uma configuração
        self.config_table.remove(Query().key == key)

    def clear_configs(self) -> None:
        # Limpa todas as configurações
        self.config_table.truncate()
