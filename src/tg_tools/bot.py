import asyncio
from typing import cast

from hydrogram import Client
from hydrogram.types import ForumTopic, Message

from tg_tools.base_tg import BaseTG
from tg_tools.config import console
from tg_tools.exceptions import TGToolsError
from tg_tools.utils import get_link_info, handle_floodwait


# -----------------------------
# Bot
# -----------------------------
class Bot(BaseTG):
    MESSAGE_TYPES = (
        "all",
        "text",
        "video",
        "photo",
        "voice",
        "audio",
        "animation",
        "document",
        "sticker",
    )

    def __init__(self, api_id: str, api_hash: str, bot_token: str) -> None:
        super().__init__(
            Client("bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
        )

    async def verify_token(self) -> None:
        try:
            async with self.client:
                user = await self.client.get_me()
                console.log(f"[green]Token verificado! Bot: {user.first_name}[/green]")
        except Exception as e:
            raise TGToolsError(f"Erro ao verificar token! Erro {e}")

    async def copy_messages(
        self,
        link: str,
        number_files: int,
        to_chat_id: int | str,
        delay: float,
        media_type: str,
        verify_messages: bool,
        filter_caption_includes: list[str] | None,
        test_mode: bool,
    ) -> None:
        """
        Copia mensagens do link informado para o chat id informado.
        """

        chat_id, msg_thread_id, start_msg_id = get_link_info(link)

        await self.verify_chat_id(chat_id)
        await self.verify_chat_id(to_chat_id)

        async with self.client:
            console.log(
                f"[blue]Copiando mensagens! Chat: {chat_id}, Chat de destino: {to_chat_id}, Quantidade: {number_files}[/blue]"
            )

            async def enviar_mensagem(
                msg: Message,
            ) -> tuple[Message | None, bool] | tuple[None, None]:
                media_type_all = media_type == "all"
                message_media_type = None

                if (media_type_all or media_type == "document") and msg.document:
                    message_media_type = "document"
                    if not test_mode:
                        return (
                            await handle_floodwait(
                                lambda: self.client.send_document(
                                    to_chat_id,
                                    document=msg.document.file_id,
                                    caption=msg.caption,
                                    caption_entities=msg.caption_entities,
                                    reply_to_message_id=msg.id,
                                )
                            ),
                            False,
                        )

                if (media_type_all or media_type == "video") and msg.video:
                    message_media_type = "video"
                    if not test_mode:
                        return (
                            await handle_floodwait(
                                lambda: self.client.send_video(
                                    to_chat_id,
                                    video=msg.video.file_id,
                                    caption=msg.caption,
                                    caption_entities=msg.caption_entities,
                                    reply_to_message_id=msg.id,
                                )
                            ),
                            False,
                        )

                if (media_type_all or media_type == "animation") and msg.animation:
                    message_media_type = "animation"
                    if not test_mode:
                        return (
                            await handle_floodwait(
                                lambda: self.client.send_animation(
                                    to_chat_id,
                                    animation=msg.animation.file_id,
                                    reply_to_message_id=msg.id,
                                )
                            ),
                            False,
                        )

                if (media_type_all or media_type == "sticker") and msg.sticker:
                    message_media_type = "sticker"
                    if not test_mode:
                        return (
                            await handle_floodwait(
                                lambda: self.client.send_sticker(
                                    to_chat_id,
                                    sticker=msg.sticker.file_id,
                                    reply_to_message_id=msg.id,
                                )
                            ),
                            False,
                        )

                if (media_type_all or media_type == "voice") and msg.voice:
                    message_media_type = "voice"
                    if not test_mode:
                        return (
                            await handle_floodwait(
                                lambda: self.client.send_voice(
                                    to_chat_id,
                                    voice=msg.voice.file_id,
                                    caption=msg.caption,
                                    caption_entities=msg.caption_entities,
                                    reply_to_message_id=msg.id,
                                )
                            ),
                            False,
                        )

                if (media_type_all or media_type == "audio") and msg.audio:
                    message_media_type = "audio"
                    if not test_mode:
                        return (
                            await handle_floodwait(
                                lambda: self.client.send_audio(
                                    to_chat_id,
                                    audio=msg.audio.file_id,
                                    caption=msg.caption,
                                    caption_entities=msg.caption_entities,
                                    reply_to_message_id=msg.id,
                                )
                            ),
                            False,
                        )

                if (media_type_all or media_type == "text") and msg.text:
                    message_media_type = "text"
                    if not test_mode:
                        return (
                            await handle_floodwait(
                                lambda: self.client.send_message(
                                    to_chat_id,
                                    text=msg.text,
                                    entities=msg.entities,
                                    reply_to_message_id=msg.id,
                                )
                            ),
                            False,
                        )

                if (media_type_all or media_type == "photo") and msg.photo:
                    message_media_type = "photo"
                    if not test_mode:
                        return (
                            await handle_floodwait(
                                lambda: self.client.send_photo(
                                    to_chat_id,
                                    photo=msg.photo.file_id,
                                    caption=msg.caption,
                                    caption_entities=msg.caption_entities,
                                    reply_to_message_id=msg.id,
                                )
                            ),
                            False,
                        )

                # if test_mode, devolve a própria msg para marcação como enviada
                if test_mode and message_media_type:
                    return msg, False

                return None, True

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
                total_message_ids = len(messages)
                valid_messages: list[int] = []

                for index, msg in enumerate(messages):
                    if topic and (topic.id != msg.message_thread_id):
                        continue

                    # filtros
                    if filter_caption_includes and msg.caption:
                        if not any(
                            f.lower() in msg.caption.lower()
                            for f in filter_caption_includes
                        ):
                            console.log(
                                f"[red]Caption não contém os filtros {filter_caption_includes} ({index + 1}/{total_message_ids})! ID: {msg.id}[/red]"
                            )
                            continue

                    try:
                        response, skip = await handle_floodwait(
                            enviar_mensagem, msg=msg
                        )
                    except Exception as e:
                        skip = True
                        console.log(
                            f"[red]Erro ao copiar mensagem ({index + 1}/{total_message_ids})! Erro {e}[/red]"
                        )

                    finally:
                        if skip:
                            pass
                        elif response:
                            valid_messages.append(msg.id)
                            console.log(
                                f"[green]Mensagem copiada ({index + 1}/{total_message_ids})! ID: {msg.id}[/green]"
                            )
                        else:
                            console.log(
                                f"[red]Mensagem inválida ou excluída ({index + 1}/{total_message_ids})! ID: {msg.id}[/red]"
                            )

                        console.log(f"[blue]Aguardando {delay} segundo(s)...[/blue]")
                        await asyncio.sleep(delay)

                total_valid_messages = len(valid_messages)
                console.log(
                    f"[green]Mensagens copiadas ({total_valid_messages}/{number_files_local})! Chat: {chat_id}[/green]"
                )

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
                        "[yellow]Verificando mensagens novamente por conteúdos ausentes...[/yellow]"
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
