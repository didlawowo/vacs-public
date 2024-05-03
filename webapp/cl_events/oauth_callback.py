import chainlit as cl
from typing import Optional, Dict

from sunholo.utils import load_config
from sunholo.database.uuid import generate_uuid_from_object_id
from .log import log
configs, filename = load_config("config/users_config.yaml")

def find_user_group(raw_user_data: Dict[str, str]):
    for group in configs['user_groups']:
        # 1. Check for domain match if 'domain' is specified and matches 'hd'
        if group.get('domain') and 'hd' in raw_user_data and raw_user_data['hd'] == group['domain']:
            return group
        # 2. Email Domain Match
        elif group.get('domain') and 'email' in raw_user_data:  
            email_domain = raw_user_data['email'].split('@')[-1]  # Extract domain from email
            if email_domain == group['domain']:
                return group
        # 3. Check for email match if 'emails' is specified
        elif any(email for email in group.get('emails', []) if email == raw_user_data['email']):
            return group
    return None

def oauth_callback_logic(
  provider_id: str,
  token: str,
  raw_user_data: Dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:
  log.info(f"OAuth Login attempt: {raw_user_data}")
  user_group = find_user_group(raw_user_data)
  identifier_user = str(generate_uuid_from_object_id(raw_user_data["email"]))
  if user_group:
      group_id = user_group.get('name', raw_user_data["name"])
      identifier = f"{group_id}-{identifier_user}"
      role = user_group['role']
      tags = user_group['tags']
  else:
      # Assign default or free user based on provider
      group_key = 'default_user' if provider_id == "google" else 'free_user'
      user_group = configs[group_key]
      identifier = f"{group_key}-{identifier_user}"
      role = user_group['role']
      tags = user_group['tags']

  return cl.User(
      identifier=identifier, 
      metadata={
          "role": role,
          "provider": provider_id,
          "tags": tags,
          "picture_url": raw_user_data.get("picture"),
          "image": raw_user_data.get("image") or raw_user_data.get("picture"),
          "hd": raw_user_data.get("hd"),
          "locale": raw_user_data.get("locale"),
          "email": raw_user_data["email"]
      }
  )


# {'id': '103351755882120083094', 
# 'email': 'm@sunholo.com', 
# 'verified_email': True, 
# 'name': 'Mark Sunholo', 
# 'given_name': 'Mark', 
# 'family_name': 'Sunholo', 
# 'picture': 'https://lh3.googleusercontent.com/a/ACg8ocLpnFjQyMEZVPs_1ulSzj3kiQFDnP1N8uLTFEX4UfjIKJA=s96-c', 
# 'locale': 'en', 
# 'hd': 'sunholo.com'}