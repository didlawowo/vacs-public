import chainlit as cl
from sunholo.utils import load_config

from .log import log

configs, filename = load_config("config/llm_config.yaml")

def to_proper_case(s):
    return ' '.join(word.capitalize() for word in s.replace('_', ' ').replace('-', ' ').split())

print(configs)

def craft_description(config):
    description = config.get('description')

    if description is None:
        description = f"VAC: {config.get('agent')} LLM: {config.get('llm')}"

    return description

def create_chat_profile(name, config):
    config = configs[name]
    return cl.ChatProfile(
        name=config.get('display_name', name),
        markdown_description=craft_description(config),
        icon=config.get("avatar_url", "public/logo_light.png")
    )

def tailor_chat_profiles(tags):
    # Check if tags is None or a list of strings
    log.info(f"Chat profile tags: {tags}")

    chat_profiles = []
    for name, config in configs.items():
        profile_tags = config.get("tags", [])  # Extract tags from config

        # Matching Logic (Choose one option below)
        if "admin" in tags:  # Option 1:  Show all profiles if an admnin tag
            match = True  
        else:
            match = False
            if profile_tags:
                match = any(tag in profile_tags for tag in tags)  # Option 2: Match any tag

        if match:
            log.info(f"Matching tag: {name} in {profile_tags} for {tags}")
            chat_profile = create_chat_profile(name, config)
            chat_profiles.append(chat_profile)
        else:
            log.info(f"No match for {name} in {profile_tags} for {tags}")

    return chat_profiles




async def chat_profile_logic(current_user: cl.User):
    log.info(f"chat_profile_logic checking current_user.metadata.role: {current_user.metadata}")
    if current_user.metadata["role"] == "ADMIN":
        admin_profiles = tailor_chat_profiles(["admin"])
        return admin_profiles
    elif current_user.metadata["role"] == "USER":
        return tailor_chat_profiles(["free"])
    elif current_user.metadata["role"] == "eduvac":
        return tailor_chat_profiles(["eduvac"])
    else:
        free_profiles = tailor_chat_profiles(["free"])
        return free_profiles
    #TODO: different chat_profiles based on current_user.tags
    return tailor_chat_profiles()
