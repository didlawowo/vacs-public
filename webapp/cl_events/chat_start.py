import chainlit as cl
from .config import lookup_config, lookup_settings
from .avatar import set_avatar
from .log import log

async def on_chat_start_logic():
    app_user = cl.user_session.get("user")
    chat_profile = cl.user_session.get("chat_profile")
    config = lookup_config(chat_profile)
    settings = lookup_settings(chat_profile)
    memory = list()
    
    # sets the avatars for the chat
    await set_avatar()

    cl.user_session.set("memory", memory)

    if settings:
        log.info(f"Setting chat settings: {settings}")
        await cl.ChatSettings(settings).send()

    log.info(f"Chat profile starting with {app_user.identifier}, ChatProfile: {chat_profile} with config: {config}")
    default_msg = f"Start chatting with {chat_profile} below"
    await cl.Message(
        author=chat_profile,
        content=config.get('description', default_msg),
    ).send()


