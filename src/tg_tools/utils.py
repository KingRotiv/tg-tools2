import asyncio
import base64
import re
from io import BytesIO
from mimetypes import guess_extension
from pathlib import Path
from typing import Callable

import pathvalidate
from hydrogram.errors.exceptions import FloodWait
from hydrogram.types import Message
from PIL import Image

from tg_tools.config import console
from tg_tools.exceptions import TGToolsError

THUMBNAIL_MAX_SIZE = 200 * 1024
THUMBNAIL_MAX_WIDTH = 320
THUMBNAIL_MAX_HEIGHT = 320
THUMBNAIL_FORMAT = "JPEG"


def format_size(size_in_bytes: int) -> str:
    # Definindo as unidades de tamanho
    units = ["B", "KB", "MB", "GB", "TB"]

    # Inicializa a unidade em "B"
    size = size_in_bytes
    unit_index = 0

    # Converte para unidades maiores até o valor ser menor que 1024
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    # Retorna o valor formatado com 2 casas decimais
    return f"{size:.2f} {units[unit_index]}"


def file_thumbnail_to_base64(file_path: str | Path) -> str:
    try:
        with Image.open(file_path) as img:

            # Verifica o tamanho da imagem
            size = Path(file_path).stat().st_size
            if size > THUMBNAIL_MAX_SIZE:
                raise TGToolsError(
                    f"Tamanho inválido! Tamanho: {format_size(size)} (máximo: {format_size(THUMBNAIL_MAX_SIZE)}), Arquivo: {file_path}"
                )

            # Verifica as dimensões da imagem
            width, height = img.size
            if width > THUMBNAIL_MAX_WIDTH or height > THUMBNAIL_MAX_HEIGHT:
                raise TGToolsError(
                    f"Dimensões inválidas! Dimensões: {width}x{height} (máximo: {THUMBNAIL_MAX_WIDTH}x{THUMBNAIL_MAX_HEIGHT}), Arquivo: {file_path}"
                )

            # Verifica o formato da imagem
            if img.format != THUMBNAIL_FORMAT:
                raise TGToolsError(
                    f"Formato inválido! Formato: {img.format} (esperado: {THUMBNAIL_FORMAT}), Arquivo: {file_path}"
                )

            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

    except FileNotFoundError:
        raise TGToolsError(f"Arquivo de thumbnail não encontrado: {file_path}")

    except Exception as e:
        raise TGToolsError(f"Erro ao ler thumbnail! Erro: {e}, Arquivo: {file_path}")


def file_thumbnail_base64_to_bytes(string: str) -> bytes:
    return base64.b64decode(string)


def thumbnail_base64_show(base64_string: str) -> None:
    try:
        img_bytes = BytesIO(base64.b64decode(base64_string))
        img = Image.open(img_bytes)
        img.show()
    except Exception as e:
        raise TGToolsError(f"Erro ao exibir thumbnail: {e}")


def search_files(path: Path | str, formats: list[str]) -> list[Path]:
    files = []

    if not isinstance(path, Path):
        path = Path(path)

    if path.is_file() and path.suffix[1:] in formats:
        files = [path]
    else:
        for format in formats:
            tmp = [
                arq if arq.is_file() else None for arq in path.glob(f"**/*.{format}")
            ]
            files.extend(list(filter(None, tmp)))

    return files


def get_link_info(link: str) -> tuple[str | int, int | None, int]:
    """
    Retorna o chat_id, msg_thread_id e msg_id a partir de um link.
    """

    regex_canal = r"^https?:\/\/t.me(?:\/c)?\/(\w+)\/(\d+)\/?$"
    search_canal = re.search(regex_canal, link)
    regex_forum_topitc = r"^https?:\/\/t.me(?:\/c)?\/(\w+)\/(\d+)\/(\d+)\/?$"
    search_forum_topitc = re.search(regex_forum_topitc, link)
    regex_bot = r"^tg:\/\/openmessage\?user_id=(\w+)&message_id=(\d+)$"
    search_bot = re.search(regex_bot, link)

    msg_thread_id = None

    if search_canal:
        chat_id = search_canal.group(1)
        if chat_id.isnumeric():
            chat_id = int("-100" + chat_id)
        msg_id = int(search_canal.group(2))

    elif search_forum_topitc:
        chat_id = search_forum_topitc.group(1)
        if chat_id.isnumeric():
            chat_id = int("-100" + chat_id)
        msg_thread_id = int(search_forum_topitc.group(2))
        msg_id = int(search_forum_topitc.group(3))

    elif search_bot:
        chat_id = search_bot.group(1)
        msg_id = int(search_bot.group(2))

    else:
        raise TGToolsError(f"Link inválido! Link: {link}")

    return chat_id, msg_thread_id, msg_id


def delete_file(file: Path | str) -> None:
    if isinstance(file, str):
        file = Path(file)
    if not file.is_file():
        console.log(f"[red]Arquivo {file} não é um arquivo!![/red]")
        return
    try:
        file.unlink()
        console.log(f"[green]Arquivo deletado! Arquivo: {file}[/green]")
    except Exception as e:  # pragma: no cover - IO errors
        console.log(f"[red]Erro ao deletar arquivo! Erro {e}[/red]")


def guess_extension_from_name_or_mime(file_name: str, mime_type: str | None) -> str:
    if file_name and "." in file_name:
        return f".{file_name.split('.')[-1]}"
    if mime_type:
        ext = guess_extension(mime_type)
        if ext:
            return ext
    return ".unknown"


def sanitize_filename(candidate: str) -> str:
    return pathvalidate.sanitize_filename(candidate, max_len=200)


async def handle_floodwait(func: Callable, *args, limit: int = 3, **kwargs):
    """Tenta executar `func(*args, **kwargs)` e trata FloodWait esperando o tempo indicado."""
    for _ in range(limit):
        try:
            result = func(*args, **kwargs)
            # se func retornar coroutine, await
            if asyncio.iscoroutine(result):
                return await result
            return result
        except FloodWait as e:
            wait = getattr(e, "value", None) or getattr(e, "seconds", None) or 1
            console.log(f"[yellow]FloodWait! Aguardando {wait} segundo(s)...[/yellow]")
            await asyncio.sleep(wait)
        except Exception:
            # re-raise outras exceções para o chamador tratar
            raise

    raise TGToolsError("Limite de FloodWait atingido!")


def caption_filters(msg: Message, filters: list[str] | None) -> bool:
    if not filters:
        return True
    if not msg.caption:
        return False
    lower_caption = msg.caption.lower()
    for f in filters:
        if f.lower() in lower_caption:
            return True
    return False
