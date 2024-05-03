import chainlit as cl
from .config import lookup_config, convert_field
from .sources import create_doc_elements, stream_sources
import os
from .log import log
from sunholo.database.alloydb import get_sources_from_docstore_async

import asyncio

# "run", "tool", "llm", "embedding", "retrieval", "rerank", "undefined"
@cl.step(name="Getting sample documents", type="tool")
async def fetch_sample_docs(settings):
    chat_profile = cl.user_session.get("chat_profile")

    msg = cl.Message(author=chat_profile, content="")
    await msg.send()

    config = lookup_config(chat_profile)
    # to a list of filters
    source_filters = convert_field(settings.get("source_filters"))
    search_type = "AND" if settings.get("source_filters_and_or", False) else "OR"
    matching_files = None

    if source_filters:
        try:
            matching_files = await get_sources_from_docstore_async(source_filters, vector_name=config["name"], search_type=search_type)
        except Exception as err:
            log.warning(f"Error looking for alloydb docs - {str(err)}")
            await msg.stream_token(f"\nError looking for alloydb docs - {str(err)}\nNo files found matching the source filters: {source_filters}.\nResetting filters.")
            settings["source_filters"] = ""

            return msg
        
    if not matching_files:
        # Handle the case where no files match the filters
        await msg.stream_token(f"\nError: No files found matching the source filters: {source_filters}. Resetting filters.")
        settings["source_filters"] = ""

        return msg
        
    await msg.stream_token(f"\nSample files matching filters {source_filters} {(search_type)}:")
    
    element_vars = []
    for j, doc in enumerate(matching_files):
        if j > 100:
            break
        is_url = False
        source = doc.metadata.get("source")
        objectId = doc.metadata.get("objectId")
        name = os.path.basename(source)
        if doc.metadata.get("bucketId"):
            bucket_id = doc.metadata.get("bucketId")
            source_uri = f'gs://{bucket_id}/{source}'
            object_uri = f'gs://{bucket_id}/{objectId}'
            name = os.path.basename(objectId)
        elif doc.metadata.get("url"):
            is_url = True
            source_uri = doc.metadata.get("url")
            object_uri = source_uri
            name = source_uri
            
        if source_uri:
            element_vars.append({"name": name,
                                 "source_uri": source_uri,
                                 "object_uri": object_uri,
                                 "source": source, 
                                 "objectId": objectId, 
                                 "is_url": is_url})                  

    # get unique sources
    shown_source = set()
    for ele in element_vars:
        element = ele.get('source_uri') if ele.get('is_url') else os.path.basename(ele.get('source'))
        if element not in shown_source:
            shown_source.add(element)
            if len(shown_source) < 10:
                await msg.stream_token(f"\n * {element}\n")

    cl.user_session.set("latest_sources_elements", element_vars)
    log.info(f"There are [{len(element_vars)}] documents matching filters {source_filters} ({search_type})")
    
    await stream_sources(msg, element_vars)
    return msg

async def setup_agent_logic(settings):
    chat_profile = cl.user_session.get("chat_profile")

    cl.user_session.set("settings", settings)

    if settings.get("source_filters"):
        # Check source filter validity
        msg = await fetch_sample_docs(settings)
    else:
        msg = cl.Message(author=chat_profile, content="")
        await msg.send()

    await msg.stream_token("\n\nCurrent settings configuration:") 
    for key, value in settings.items():
        log.info(f"msg elements - setup_agent_logic: {msg.elements}")
        await msg.stream_token(f"\n  * {key}: {value}")
