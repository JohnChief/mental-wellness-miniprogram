import json
import os
import re
from typing import Any, Optional

import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
from openai import OpenAI


try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
BOT_NAME = os.getenv("BOT_NAME", "Codex")
BOT_SYSTEM_PROMPT = os.getenv(
    "BOT_SYSTEM_PROMPT",
    "你是一个在飞书群里参与产品和技术讨论的 AI 助手。回复要简洁、具体、可执行。",
)

openai_client = OpenAI()
feishu_client = (
    lark.Client.builder()
    .app_id(FEISHU_APP_ID)
    .app_secret(FEISHU_APP_SECRET)
    .log_level(lark.LogLevel.INFO)
    .build()
)


def require_env() -> None:
    missing = [
        name
        for name, value in {
            "FEISHU_APP_ID": FEISHU_APP_ID,
            "FEISHU_APP_SECRET": FEISHU_APP_SECRET,
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def get_attr(obj: Any, path: str, default: Any = None) -> Any:
    current = obj
    for part in path.split("."):
        if current is None:
            return default
        current = getattr(current, part, default)
    return current


def parse_text_content(raw_content: Optional[str]) -> str:
    if not raw_content:
        return ""

    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        return raw_content.strip()

    text = content.get("text", "") if isinstance(content, dict) else ""
    return re.sub(r"<at[^>]*>.*?</at>", "", text).strip()


def is_bot_sender(event: Any) -> bool:
    sender_type = get_attr(event, "sender.sender_type", "")
    return str(sender_type).lower() in {"app", "bot"}


def should_reply(event: Any) -> bool:
    chat_type = get_attr(event, "message.chat_type", "")
    mentions = get_attr(event, "message.mentions", None)

    if is_bot_sender(event):
        return False

    if chat_type == "p2p":
        return True

    return bool(mentions)


def ask_openai(user_text: str) -> str:
    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": BOT_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    )
    return response.output_text.strip()


def send_text(chat_id: str, text: str) -> None:
    request = (
        CreateMessageRequest.builder()
        .receive_id_type("chat_id")
        .request_body(
            CreateMessageRequestBody.builder()
            .receive_id(chat_id)
            .msg_type("text")
            .content(json.dumps({"text": text}, ensure_ascii=False))
            .build()
        )
        .build()
    )

    response = feishu_client.im.v1.message.create(request)
    if not response.success():
        raise RuntimeError(
            f"Failed to send Feishu message: code={response.code}, msg={response.msg}, log_id={response.get_log_id()}"
        )


def handle_message(data: Any) -> None:
    event = data.event
    if not should_reply(event):
        return

    chat_id = get_attr(event, "message.chat_id", "")
    raw_content = get_attr(event, "message.content", "")
    user_text = parse_text_content(raw_content)

    if not chat_id or not user_text:
        return

    try:
        answer = ask_openai(user_text)
    except Exception as exc:
        answer = f"{BOT_NAME} 调用 OpenAI 失败：{exc}"

    try:
        send_text(chat_id, answer)
    except Exception as exc:
        print(f"Failed to reply in Feishu: {exc}")


def main() -> None:
    require_env()

    event_handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(handle_message)
        .build()
    )

    ws_client = lark.ws.Client(
        FEISHU_APP_ID,
        FEISHU_APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO,
    )

    print("Feishu bot started. Mention the bot in Feishu to chat.")
    ws_client.start()


if __name__ == "__main__":
    main()
