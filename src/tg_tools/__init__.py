import asyncio
from argparse import ArgumentParser, ArgumentTypeError

import pyfiglet

from tg_tools.bot import Bot
from tg_tools.config import console
from tg_tools.db import DBManager
from tg_tools.exceptions import TGToolsError
from tg_tools.user_bot import Userbot
from tg_tools.utils import (
    file_thumbnail_base64_to_bytes,
    file_thumbnail_to_base64,
    thumbnail_base64_show,
)
from tg_tools.version import __version__


# -----------------------------
# CLI
# -----------------------------
class CLI:
    KEYS_VALIDES = [
        "session-string",
        "api-id",
        "api-hash",
        "bot-token",
        "thumbnail",
    ]

    def __init__(self) -> None:
        self.db = DBManager()

    def get(self, key: str) -> str | None:
        return self.db.get_config(key)

    async def set(self, key: str, value: str) -> None:
        if key == "session-string":
            userbot = Userbot(value)
            await userbot.verify_session()
        if key == "thumbnail":
            value = file_thumbnail_to_base64(value)
        self.db.set_config(key, value)

    def remove(self, key: str) -> None:
        self.db.remove_config(key)

    def reset(self) -> None:
        self.db.clear_configs()


# -----------------------------
# CLI init
# -----------------------------
async def init() -> None:
    cli = CLI()

    # --- ASCII Art --- #
    ascii_art = pyfiglet.figlet_format("TG-TOOLS")
    console.print(ascii_art)

    # --- Funções auxiliares --- #
    def print_test_mode(test_mode: bool):
        if test_mode:
            console.log("[yellow]Modo de teste ativado![/yellow]")

    # ---- Tipos personalizados --- #
    def chat_id(value: str) -> int | str:
        if value.isdigit():
            return int(value)
        elif len(value) > 1 and value[0] == "-" and value[1:].isdigit():
            return int(value)
        return value

    def number_files(value: str, limit: int) -> int:
        if value.isdigit() and int(value) > 0 and int(value) <= limit:
            return int(value)
        raise ArgumentTypeError(
            f"O number_files deve ser um inteiro entre 1 e {limit}."
        )

    def number_files_userbot(value: str) -> int:
        return number_files(value, limit=Userbot.LIMIT_GET_MESSAGES)

    def number_files_bot(value: str) -> int:
        return number_files(value, limit=Bot.LIMIT_GET_MESSAGES)

    # --- Parsers config --- #
    parser = ArgumentParser()
    parser.add_argument("-V", "--version", action="version", version=f"v{__version__}")
    parser.add_argument(
        "-r", "--reset", action="store_true", help="Limpa todas as configurações."
    )
    parser.add_argument(
        "-s",
        "--status",
        action="store_true",
        help="Verifica o status das configurações.",
    )
    parser.add_argument(
        "--create-session-string",
        action="store_true",
        help="Cria uma nova sessão e a configura.",
    )
    parser.add_argument(
        "--get-db-file",
        action="store_true",
        help="Obtém o caminho do arquivo do banco de dados.",
    )
    subparsers = parser.add_subparsers(dest="command")

    get_parser = subparsers.add_parser("get", help="Obtém o valor de uma configuração.")
    get_parser.add_argument(
        "key", type=str, choices=cli.KEYS_VALIDES, help="A chave da configuração."
    )

    set_parser = subparsers.add_parser("set", help="Define uma configuração.")
    set_parser.add_argument(
        "key", type=str, choices=cli.KEYS_VALIDES, help="A chave da configuração."
    )
    set_parser.add_argument("value", type=str, help="O valor da configuração.")

    remove_parser = subparsers.add_parser("remove", help="Remove uma configuração.")
    remove_parser.add_argument(
        "key", type=str, choices=cli.KEYS_VALIDES, help="A chave da configuração."
    )

    # --- Parsers user bot --- #
    upload_media_parser = subparsers.add_parser(
        "upload-media", help="Envia os arquivos para um chat."
    )
    upload_media_parser.add_argument(
        "path_or_file", type=str, help="O arquivo ou pasta com arquivos."
    )
    upload_media_parser.add_argument(
        "chat_id", type=chat_id, help="O id do chat para enviar os arquivos."
    )
    upload_media_parser.add_argument(
        "media_type",
        type=str,
        choices=Userbot.MESSAGE_TYPES[1:],
        help="O tipo de arquivo para enviar.",
    )
    upload_media_parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        default=False,
        help="Apaga os arquivos locais após enviar.",
    )
    upload_media_parser.add_argument(
        "-ln",
        "--listen-new-files",
        action="store_true",
        default=False,
        help="Escuta novos arquivos na pasta e envia automaticamente.",
    )
    upload_media_parser.add_argument(
        "--test-mode",
        action="store_true",
        default=False,
        help="Não envia de fato os arquivos para o chat.",
    )

    download_media_parser = subparsers.add_parser(
        "download-media", help="Baixa os arquivos de um chat."
    )
    download_media_parser.add_argument(
        "link", type=str, help="O link para baixar os arquivos."
    )
    download_media_parser.add_argument(
        "number_files",
        type=number_files_userbot,
        help="O número de arquivos a serem baixados.",
    )
    download_media_parser.add_argument(
        "path", type=str, help="O caminho para salvar os arquivos."
    )
    download_media_parser.add_argument(
        "-n",
        "--name",
        type=str,
        choices=["file_name", "caption"],
        default="file_name",
        help="O tipo de nome a ser definido para os arquivos baixados.",
    )
    download_media_parser.add_argument(
        "-mt",
        "--media-type",
        type=str,
        choices=Userbot.MESSAGE_TYPES,
        default="all",
        help="O tipo de arquivo a ser baixado.",
    )
    download_media_parser.add_argument(
        "-vm",
        "--verify-messages",
        action="store_true",
        default=False,
        help="Verifica se as mensagens são válidas, não contando mensagens excluídas ou sem conteúdo.",
    )
    download_media_parser.add_argument(
        "-fc",
        "--filter-caption-includes",
        nargs="+",
        type=str,
        help="Filtra as mensagens pelo conteúdo do caption. (Não diferencia maiusculas e minusculas).",
    )
    download_media_parser.add_argument(
        "--test-mode",
        action="store_true",
        default=False,
        help="Modo de teste, baixa o arquivo vázio.",
    )

    # --- Parsers bot --- #
    copy_messages_parser = subparsers.add_parser(
        "copy-messages", help="Copia mensagens de um chat para outro chat."
    )
    copy_messages_parser.add_argument(
        "link", type=str, help="O link da mensagem inicial."
    )
    copy_messages_parser.add_argument(
        "number_files",
        type=number_files_bot,
        help="O número de mensagens a serem copiadas.",
    )
    copy_messages_parser.add_argument(
        "to_chat_id", type=chat_id, help="O id do chat de destino."
    )
    copy_messages_parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=1,
        help="Tempo de espera em segundos entre envio das mensagens.",
    )
    copy_messages_parser.add_argument(
        "-mt",
        "--media-type",
        type=str,
        choices=Bot.MESSAGE_TYPES,
        default="all",
        help="O tipo de arquivo a ser enviado.",
    )
    copy_messages_parser.add_argument(
        "-vm",
        "--verify-messages",
        action="store_true",
        default=False,
        help="Verifica se as mensagens são válidas, não contando mensagens excluídas ou sem conteúdo.",
    )
    copy_messages_parser.add_argument(
        "-fc",
        "--filter-caption-includes",
        nargs="+",
        type=str,
        help="Filtra as mensagens pelo conteúdo do caption. (Não diferencia maiusculas e minusculas).",
    )
    copy_messages_parser.add_argument(
        "--test-mode",
        action="store_true",
        default=False,
        help="Modo de teste, imprime a mensagem.",
    )

    args = parser.parse_args()

    # --- Execução --- #

    # Configuração
    if args.reset:
        cli.reset()
        console.print("Todas as configurações foram resetadas.")

    elif args.status:
        for key in cli.KEYS_VALIDES:
            console.print(f"{key} -> {'OK' if cli.get(key) else None}")

    elif args.create_session_string:
        cli = CLI()
        api_id = cli.get("api-id")
        api_hash = cli.get("api-hash")
        session_old = cli.get("session-string")

        if not api_id:
            console.print("É necessário configurar sua api-id antes.")
        elif not api_hash:
            console.print("É necessário configurar sua api-hash antes.")
        elif not session_old:
            session = await Userbot.create_session_string(api_id, api_hash)
            await cli.set("session-string", session)
        else:
            console.print(
                "Sessão já existente! Para criar outra, remova a atual primeiro."
            )

    elif args.get_db_file:
        cli = CLI()
        console.print(f"Localização do banco de dados -> {cli.db.db_full_path}")

    elif args.command == "set":
        try:
            await cli.set(args.key, args.value)
            console.print(f"{args.key} -> Configurado com sucesso.")
        except Exception as e:
            console.log(f"[red]Erro ao configurar {args.key}: {e}[/red]")

    elif args.command == "get":
        value = cli.get(args.key)
        match (args.key):
            case "thumbnail" if value:
                console.print(f"{args.key} -> Abrindo...")
                thumbnail_base64_show(value)
            case _:
                if args.key == "session-string" and value:
                    userbot = Userbot(value)
                    await userbot.verify_session()
                elif (
                    (api_id := cli.get("api-id"))
                    and (api_hash := cli.get("api-hash"))
                    and args.key == "bot-token"
                    and value
                ):
                    bot = Bot(api_id, api_hash=api_hash, bot_token=value)
                    await bot.verify_token()

                console.print(f"{args.key} -> {value}")

    elif args.command == "remove":
        cli.remove(args.key)
        console.print(f"{args.key} -> Removido com sucesso.")

    # Userbot
    elif args.command == "upload-media":
        media_type_formats = {
            "video": ["mp4", "mov", "mkv", "m4v"],
            "photo": ["jpg", "jpeg", "png", "webp"],
            "voice": ["ogg", "mp3", "wav", "m4a"],
            "audio": ["mp3", "wav", "m4a"],
            "animation": ["mp4", "mov", "mkv", "m4v"],
            "document": ["*"],
        }

        if session_string := cli.get("session-string"):
            print_test_mode(args.test_mode)
            userbot = Userbot(session_string)
            await userbot.verify_session()

            thumbnail = cli.get("thumbnail")
            if thumbnail:
                thumbnail = file_thumbnail_base64_to_bytes(thumbnail)

            await userbot.upload_media(
                args.path_or_file,
                chat_id=args.chat_id,
                formats=media_type_formats[args.media_type],
                media_type=args.media_type,
                delete=args.delete,
                listen_new_files=args.listen_new_files,
                thumbnail=thumbnail,  # type: ignore
                test_mode=args.test_mode,
            )
        else:
            console.print("Sessão do userbot não encontrada!")

    elif args.command == "download-media":
        if args.verify_messages and not args.filter_caption_includes:
            console.print(
                "A flag --verify-messages só pode ser usada em conjunto com --filter-caption-includes."
            )
            return

        if session_string := cli.get("session-string"):
            print_test_mode(args.test_mode)
            userbot = Userbot(session_string)
            await userbot.verify_session()

            await userbot.download_media(
                args.link,
                number_files=args.number_files,
                path=args.path,
                name=args.name,
                media_type=args.media_type,
                verify_messages=args.verify_messages,
                filter_caption_includes=args.filter_caption_includes,
                test_mode=args.test_mode,
            )
        else:
            console.print("Sessão do userbot não encontrada!")

    # Bot
    elif args.command == "copy-messages":
        if args.verify_messages and not args.filter_caption_includes:
            console.print(
                "A flag --verify-messages só pode ser usada em conjunto com --filter-caption-includes."
            )
            return

        if (
            (api_id := cli.get("api-id"))
            and (api_hash := cli.get("api-hash"))
            and (bot_token := cli.get("bot-token"))
        ):
            print_test_mode(args.test_mode)
            bot = Bot(api_id, api_hash=api_hash, bot_token=bot_token)
            await bot.verify_token()

            await bot.copy_messages(
                args.link,
                number_files=args.number_files,
                to_chat_id=args.to_chat_id,
                delay=args.delay,
                media_type=args.media_type,
                verify_messages=args.verify_messages,
                filter_caption_includes=args.filter_caption_includes,
                test_mode=args.test_mode,
            )
        else:
            console.print(
                "Configurações do bot incorretas! Configure: api_id, api_hash e bot_token."
            )


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    try:
        asyncio.run(init())
    except TGToolsError as ex:
        console.print(f"[red]Não foi possível continuar -> {ex.message}[/red]")
    except KeyboardInterrupt:
        console.print("Finalizando...")
