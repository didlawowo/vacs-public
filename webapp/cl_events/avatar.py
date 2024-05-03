import chainlit as cl
from .config import lookup_config
from .log import log

async def set_avatar():
    app_user        = cl.user_session.get("user")
    chat_profile    = cl.user_session.get("chat_profile")
    config          = lookup_config(chat_profile)

    log.info(f"avatar_user: {app_user}")

    avatar_url = config.get("avatar_url")
    if not avatar_url:
        avatar_url = "../public/logo_dark.png"
    await cl.Avatar(
        name=chat_profile,
        url=avatar_url,
    ).send()

    # Check if 'picture_url' exists and log it
    picture_url = app_user.metadata.get('picture_url')
    if picture_url:
        log.info(f"app_user.metadata.picture_url - {picture_url}")
    else:
        log.info("No picture_url found in app_user.metadata, using the default avatar_url.")

    # Instantiate the Avatar with the picture_url or a default avatar_url
    try:
        await cl.Avatar(
            name = "You",
            url = picture_url or avatar_url,
        ).send()
    except Exception as e:
        log.error(f"Failed to create Avatar: {e}")
        await cl.Avatar(
            name = "you",
            url = "public/logo_light.png",
        ).send()