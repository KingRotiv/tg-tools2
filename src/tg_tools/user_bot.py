import asyncio
import time
from io import BytesIO
from pathlib import Path
from typing import Literal, cast

from hydrogram import Client
from hydrogram.types import ForumTopic, Message

from tg_tools.base_tg import BaseTG
from tg_tools.config import console
from tg_tools.exceptions import TGToolsError
from tg_tools.utils import (
    caption_filters,
    delete_file,
    format_size,
    get_link_info,
    guess_extension_from_name_or_mime,
    handle_floodwait,
    sanitize_filename,
    search_files,
)


# -----------------------------
# Userbot
# -----------------------------
class Userbot(BaseTG):
    MESSAGE_TYPES = (
        "all",
        "video",
        "photo",
        "voice",
        "audio",
        "animation",
        "document",
    )

    def __init__(self, session_string: str) -> None:
        super().__init__(Client("userbot", session_string=session_string))

    @staticmethod
    async def create_session_string(api_id: int | str, api_hash: str) -> str:
        """Cria uma nova sessão e exporta em formato de string."""
        try:
            console.log("[blue]Criando nova sessão...[/blue]")
            async with Client(
                "_userbot", api_id=api_id, api_hash=api_hash, in_memory=True
            ) as app:
                session = await app.export_session_string()
                console.log("[green]Sessão criada com sucesso![/green]")
                return session
        except Exception as e:
            raise TGToolsError(f"Erro ao criar sessão! Erro {e}")

    async def verify_session(self) -> None:
        """Verifica a sessão do userbot."""
        try:
            async with self.client:
                user = await self.client.get_me()
                console.log(
                    f"[green]Sessão verificada! Usuário: {user.first_name}[/green]"
                )
        except Exception as e:
            raise TGToolsError(f"Erro ao verificar sessão! Erro {e}")

    # --- Helpers para download --- #
    def _get_media_info(self, msg: Message) -> tuple[str | None, str | None]:
        """Retorna (file_name, mime_type) baseado no conteúdo da mensagem."""
        if msg.video:
            return msg.video.file_name or "", msg.video.mime_type or ""
        if msg.photo:
            return "", "image/jpeg"
        if msg.voice:
            return "", getattr(msg.voice, "mime_type", "")
        if msg.audio:
            return getattr(msg.audio, "file_name", ""), getattr(
                msg.audio, "mime_type", ""
            )
        if msg.animation:
            return getattr(msg.animation, "file_name", ""), getattr(
                msg.animation, "mime_type", ""
            )
        if msg.document:
            return getattr(msg.document, "file_name", ""), getattr(
                msg.document, "mime_type", ""
            )
        return None, None

    def _build_target_path(self, base_path: Path, raw_name: str | None) -> str:
        base = base_path.absolute().as_posix().removesuffix("/") + "/"
        if raw_name:
            sanitized = sanitize_filename(raw_name)
            return base + sanitized
        else:
            return f"{base}{time.time()}.unknown"

    async def upload_media(
        self,
        path_or_file: str | Path,
        chat_id: int | str,
        formats: list[str],
        media_type: str,
        delete: bool = False,
        listen_new_files: bool = False,
        thumbnail: bytes | None = None,
        test_mode: bool = False,
    ) -> None:
        """
        Envia arquivos para o chat id informado.
        """

        await self.verify_chat_id(chat_id)

        async with self.client:
            console.log(
                f"[blue]Enviando arquivos! Origem: {path_or_file}, Chat: {chat_id}[/blue]"
            )

            def progress(current: int, total: int) -> None:  # progress callback
                try:
                    progress_str = f"Enviando... {format_size(current)} / {format_size(total)} - {current / total * 100:.2f}%"
                    console.print(progress_str, end="\r")
                except Exception:
                    pass

            seen = set()

            while True:
                files = search_files(path_or_file, formats=formats) or []
                files = [f for f in files if f not in seen]
                length_files = len(files)
                console.log(
                    f"[blue]Total de arquivos encontrados: {length_files}, Tipo: {media_type}[/blue]"
                )

                for index, file in enumerate(files):
                    try:
                        console.log(
                            f"[blue]Enviando arquivo ({index + 1}/{length_files})! Arquivo: {file}[/blue]"
                        )

                        # thumb precisa ser BytesIO novo por envio
                        thumb_obj = BytesIO(thumbnail) if thumbnail else None

                        async def send():
                            if media_type == "video":
                                return await self.client.send_video(
                                    chat_id=chat_id,
                                    video=file.as_posix(),
                                    caption=file.name,
                                    thumb=thumb_obj,
                                    progress=progress,
                                )
                            elif media_type == "photo":
                                return await self.client.send_photo(
                                    chat_id=chat_id,
                                    photo=file.as_posix(),
                                    caption=file.name,
                                    progress=progress,
                                )
                            elif media_type == "voice":
                                return await self.client.send_voice(
                                    chat_id=chat_id,
                                    voice=file.as_posix(),
                                    caption=file.name,
                                    progress=progress,
                                )
                            elif media_type == "audio":
                                return await self.client.send_audio(
                                    chat_id=chat_id,
                                    audio=file.as_posix(),
                                    caption=file.name,
                                    thumb=thumb_obj,
                                    progress=progress,
                                )
                            elif media_type == "animation":
                                return await self.client.send_animation(
                                    chat_id=chat_id,
                                    animation=file.as_posix(),
                                    caption=file.name,
                                    thumb=thumb_obj,
                                    progress=progress,
                                )
                            elif media_type == "document":
                                return await self.client.send_document(
                                    chat_id=chat_id,
                                    document=file.as_posix(),
                                    caption=file.name,
                                    thumb=thumb_obj,
                                    progress=progress,
                                )
                            else:
                                raise TGToolsError(
                                    f"Tipo de arquivo desconhecido: {media_type}"
                                )

                        if not test_mode:
                            enviado = await handle_floodwait(send)
                        else:
                            enviado = True

                        console.log(
                            f"[green]Arquivo enviado ({index + 1}/{length_files})! Arquivo: {file}[/green]"
                        )
                        seen.add(file)

                        if enviado and delete:
                            delete_file(file)

                    except Exception as e:
                        console.log(
                            f"[red]Erro ao enviar arquivo ({index + 1}/{length_files})! Erro {e}[/red]"
                        )

                if not listen_new_files or len(files) == 0:
                    break

                await asyncio.sleep(1)

            console.log("[green]Tarefa concluída![/green]")

    async def download_media(
        self,
        link: str,
        number_files: int,
        path: str | Path,
        name: Literal["file_name", "caption"],
        media_type: str,
        verify_messages: bool,
        filter_caption_includes: list[str] | None,
        test_mode: bool,
    ) -> None:
        """ "
        Baixa arquivos do link informado.
        """

        chat_id, msg_thread_id, start_msg_id = get_link_info(link)

        await self.verify_chat_id(chat_id)

        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            path = path.parent

        async with self.client:
            console.log(
                f"[blue]Baixando arquivos! Chat: {chat_id}, Quantidade: {number_files}, Pasta: {path}, Tipo de nome: {name}, Tipo de mídia: {media_type}, Verificar mensagens: {verify_messages}, Filtros caption: {filter_caption_includes}[/blue]"
            )

            def progress(current: int, total: int) -> None:
                try:
                    progress_str = f"Baixando... {format_size(current)} / {format_size(total)} - {current / total * 100:.2f}%"
                    console.print(progress_str, end="\r")
                except Exception:
                    pass

            async def read(
                message_ids: list[int],
                number_files_local: int,
                topic: ForumTopic | None = None,
            ) -> None:
                if number_files_local == 0 or not message_ids:
                    console.log("[green]Nada a fazer neste range.[/green]")
                    return

                messages = cast(
                    list[Message],
                    await self.client.get_messages(chat_id, message_ids=message_ids),
                )

                valid_messages: list[int] = []
                total_valid_messages = 0

                for msg in messages:
                    path_verify = Path(
                        path.absolute().as_posix().removesuffix("/") + "/"
                    )

                    if not (isinstance(msg, Message) and msg.media):
                        continue

                    if topic and (topic.id != msg.message_thread_id):
                        continue

                    media_type_all = media_type == "all"

                    file_name, mime_type = self._get_media_info(msg)

                    # conta como valida só se tiver um tipo reconhecido
                    is_valid_media = media_type_all or (
                        (media_type == "video" and msg.video)
                        or (media_type == "photo" and msg.photo)
                        or (media_type == "voice" and msg.voice)
                        or (media_type == "audio" and msg.audio)
                        or (media_type == "animation" and msg.animation)
                        or (media_type == "document" and msg.document)
                    )

                    if not is_valid_media:
                        continue

                    # nome baseado em caption
                    if name == "caption" and msg.caption:
                        extension = guess_extension_from_name_or_mime(
                            file_name or "", mime_type
                        )
                        raw = (msg.caption[:200]) if msg.caption else ""
                        file_name = f"{raw}{extension}"

                    # constrói path final
                    target_path = self._build_target_path(path_verify, file_name)

                    # filtros por caption
                    if not caption_filters(msg, filter_caption_includes):
                        console.log(
                            f"[red]Caption não contém os filtros {filter_caption_includes}! Mensagem: {msg.id}[/red]"
                        )
                        continue

                    try:
                        total_valid_messages += 1
                        console.log(
                            f"[blue]Baixando arquivo ({total_valid_messages}/{number_files_local})! Mensagem: {msg.id}, Arquivo: {target_path}[/blue]"
                        )
                        if test_mode:
                            # escreve arquivo dummy em pasta .test_mode para não sujar pasta original
                            test_dir = Path(path, ".test_mode")
                            test_dir.mkdir(parents=True, exist_ok=True)
                            file_test = (
                                self._build_target_path(test_dir, file_name)
                                + ".test_mode"
                            )
                            Path(file_test).write_text("TEST MODE")
                            target_path = file_test
                        else:

                            async def download():
                                return await self.client.download_media(
                                    msg, progress=progress, file_name=target_path
                                )

                            await handle_floodwait(download)

                        valid_messages.append(msg.id)
                        console.log(
                            f"[green]Arquivo baixado ({total_valid_messages}/{number_files_local})! Mensagem: {msg.id}, Arquivo: {target_path}[/green]"
                        )

                    except Exception as e:
                        console.log(
                            f"[red]Erro ao baixar arquivo ({total_valid_messages}/{number_files_local})! Erro {e}[/red]"
                        )

                # pós-processamento: checar se precisa re-ler
                total_valid_messages = len(valid_messages)

                if (
                    verify_messages
                    and not topic
                    and total_valid_messages > 0
                    and total_valid_messages < number_files_local
                ):
                    console.log(
                        "[blue]Verificando mensagens novamente por conteúdos ausentes...[/blue]"
                    )
                    difference = number_files_local - total_valid_messages
                    last_id = valid_messages[-1] if valid_messages else message_ids[-1]
                    new_message_ids = list(range(last_id + 1, last_id + 1 + difference))
                    await read(new_message_ids, number_files_local=difference)

                if topic and total_valid_messages < number_files_local:
                    difference = number_files_local - total_valid_messages
                    last_valid_msg_id = (
                        valid_messages[-1] if valid_messages else message_ids[-1]
                    )
                    last_msg_id_topic = topic.top_message
                    range_msgs_id_topic = list(
                        range(last_valid_msg_id + 1, last_msg_id_topic)
                    )
                    total_range_msgs_id_topic = len(range_msgs_id_topic)

                    console.log(
                        "[yellow]Verificando mensagens novamente por conteúdos ausentes (tópico)...[/yellow]"
                    )
                    console.log(
                        f"[yellow]Será usado um deslocamento de {total_range_msgs_id_topic} ids no tópico a partir da mensagem: {last_valid_msg_id}[/yellow]"
                    )
                    if total_range_msgs_id_topic > self.LIMIT_GET_MESSAGES:
                        range_msgs_id_topic = range_msgs_id_topic[
                            0 : self.LIMIT_GET_MESSAGES
                        ]

                    await read(
                        range_msgs_id_topic, number_files_local=difference, topic=topic
                    )

            range_init = list(range(start_msg_id, start_msg_id + number_files))
            if not msg_thread_id:
                await read(range_init, number_files_local=number_files)
            else:
                topics = await self.client.get_forum_topics_by_id(
                    chat_id, topic_ids=msg_thread_id
                )
                if not topics:
                    raise TGToolsError(f"Tópico inexistente! ID: {msg_thread_id}")
                topic = topics[0] if isinstance(topics, list) else topics

                last_msg_id_topic = topic.top_message
                console.log(
                    f"[blue]Tópico indentificado: {topic.title}, Mensagem inicial: {start_msg_id}, Última mensagem: {last_msg_id_topic}[/blue]"
                )
                await read(range_init, number_files_local=number_files, topic=topic)
