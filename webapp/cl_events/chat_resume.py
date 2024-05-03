import chainlit as cl
from chainlit.types import ThreadDict
from .config import lookup_settings
from .log import log
from .avatar import set_avatar

async def on_chat_resume_logic(thread: ThreadDict):

    # sets the avatars for the chat
    await set_avatar()

    memory = list()

    root_messages = [m for m in thread["steps"] if m["parentId"] is None]
    for message in root_messages:
        if message["type"] == "USER_MESSAGE":       
            memory.append({"name": "Human", "content": message["output"]})
        else:
            memory.append({"name": "AI", "content": message["output"]})


    cl.user_session.set("memory", memory)
    chat_profile = cl.user_session.get("chat_profile")
    settings = lookup_settings(chat_profile)
    if settings:
        log.info(f"Resuming - Setting chat settings: {settings}")
        await cl.ChatSettings(settings).send()
