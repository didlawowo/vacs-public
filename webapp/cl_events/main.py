import chainlit as cl
import logging
from sunholo.agents import send_to_qa_async
from sunholo.streaming import generate_proxy_stream_async
from .config import lookup_config
import json

async def main_logic(message: cl.Message):
    app_user = cl.user_session.get("user")
    chat_profile = cl.user_session.get("chat_profile")
    memory = cl.user_session.get("memory")

    log.info(f"app_user: {app_user}")
    log.info(f"Got message: {message.to_dict()}")
          
    memory.append({"name": "Human", "content": message.content})

    user_input = message.content
    chat_history = memory
    message_author = app_user.identifier
    config = lookup_config(chat_profile)

    log.info(f"chat_profile: {chat_profile} {type(chat_profile)}")  
    async def stream_response():
        generate = await generate_proxy_stream_async(
            send_to_qa_async,
            user_input,
            vector_name=config["name"],
            chat_history=chat_history,
            generate_f_output=generate_chainlit_output,
            # kwargs
            stream_wait_time=0.5,
            stream_timeout=120,
            message_author=message_author,
        )
        # Stream the response from the generator
        async for part in generate():
            yield part

    avatar_url = config.get("avatar_url")
    if not avatar_url:
        avatar_url = "https://avatars.githubusercontent.com/u/128686189?s=400&u=a1d1553023f8ea0921fba0debbe92a8c5f840dd9&v=4"
    await cl.Avatar(
        name=chat_profile,
        url=avatar_url,
    ).send()

    # Create a reply message for streaming
    msg = cl.Message(author=chat_profile, content="")

    # Stream the content token by token
    async for token in stream_response():
        if token:
            # Check if token is a byte string
            if isinstance(token, bytes):
                token_str = token.decode('utf-8')  # Decoding byte string to a regular string
            else:
                token_str = token  # It's already a string
            await msg.stream_token(token_str)
            
    log.info("chanlit streaming finished")

    # Send the final message
    memory.append({"name": "AI", "content": msg.content})  
    await msg.update()
