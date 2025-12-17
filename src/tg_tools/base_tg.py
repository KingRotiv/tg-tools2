from hydrogram import Client

from tg_tools.config import console
from tg_tools.exceptions import TGToolsError


# -----------------------------
# Base client com utilitários comuns
# -----------------------------
class BaseTG:
    """Classe base para comportamentos comuns entre Userbot e Bot."""

    LIMIT_GET_MESSAGES = 200

    def __init__(self, client: Client) -> None:
        self.client = client

    async def verify_chat_id(self, chat_id: int | str) -> None:
        """Verifica se o chat existe e o cliente tem acesso."""
        try:
            async with self.client:
                await self.client.get_chat(chat_id)
                console.log(f"[green]Chat verificado! ID: {chat_id}[/green]")
        except Exception as e:
            raise TGToolsError(f"Erro ao verificar chat! Erro {e}")
