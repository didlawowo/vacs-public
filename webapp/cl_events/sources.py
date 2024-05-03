from sunholo.gcs import construct_download_link
import chainlit as cl
from .log import log
import os

async def stream_sources(msg, sources_elements):
    #log.info(f"chainlit sources: {sources_elements}")
    if sources_elements:
        log.info(f"adding chainlit sources to {msg}: [{len(sources_elements)}]")
        content = msg.content
        log.debug(f"Message content: {content}")
        msg_uris = []
        match_strings = []
        for element in sources_elements:
            #log.debug(f"checking element: {element}")
            match_name = element["name"]
            source_name = os.path.basename(element["source"])
            if match_name in content and match_name not in match_strings:
                log.info(f"found match for {match_name} - adding to msg: element: {element}")
                msg_uris.append(element)
                match_strings.append(match_name)
            if source_name in content and source_name not in match_strings:
                log.info(f"found match for source: {source_name} - adding to msg: element: {element}")
                msg_uris.append(element)
                match_strings.append(source_name)
                
        msg_elements = await create_doc_elements(msg_uris)
        if hasattr(msg, 'elements'):
            msg.elements.extend(msg_elements)
        else:
            msg.elements = msg_elements
        await msg.update()

        return f"Found [{len(msg_elements)}] documents"
        
    else:
        log.info(f"chainlit sources not added [{len(sources_elements)}]")

async def generate_chainlit_sources(bot_output: dict, key="metadata"):
    
    metadata = bot_output.get(key, None)

    source_data = []

    # parse out source data
    if metadata:
        for source_doc in metadata:
            if source_doc.get("source"):
                #log.debug(f"source_metadata: {metadata_source}")
                #TODO: more here
                source_data.append({"source": source_doc.get("source"),
                                    "objectId":source_doc.get("objectId"),
                                    "source_uri": source_doc.get("source_uri")})
    
    if source_data:
        #log.info(f"source_data: {source_data}")

        # Deduplicate source names while preserving order
        seen_sources = set()  # Track which source_names we've already seen
        unique_sources = []
        for source_doc in source_data:
            source_name = source_doc.get("objectId", None)
            if source_name and source_name not in seen_sources:
                unique_sources.append(source_doc)
                seen_sources.add(source_name)
        
        return await create_doc_elements(unique_sources)

#{"source_uri": source_uri,
# "object_uri": object_uri,
# "source": source, 
# "objectId": objectId, 
# "is_url": is_url})  

async def create_doc_elements(unique_sources: list):

    elements = []
    unique_sources_set = set()
    unique_objects_set = set()

    for citation in unique_sources:
        source_uri = citation.get("source_uri")
        source_name = citation.get("source")
        object_uri = citation.get("object_uri")
        object_name = citation.get("objectId")

        # Check and add unique source URIs
        if source_uri and source_uri not in unique_sources_set:
            unique_sources_set.add(source_uri)
            elements.append({"name": source_name, "uri": source_uri})

        # Check and add unique object URIs
        if object_uri and object_uri not in unique_objects_set:
            unique_objects_set.add(object_uri)
            elements.append({"name": object_name, "uri": object_uri})

    output_elements = []
    for cite in elements:
        source_uri = cite.get("uri")
        if source_uri.startswith("http"):
            # no file links for http links
            continue
        link, encoded_filename, signed  = construct_download_link(source_uri)
        lowf = encoded_filename.lower()
        if lowf.endswith(".pdf") and signed:
            new_element = cl.Pdf(
                    name=encoded_filename,
                    url=link,
                    # Controls how the image element should be displayed in the UI. Choices are “side” (default), “inline”, or “page”.
                    display="side",
                )
        elif (lowf.endswith(".jpeg") or lowf.endswith(".jpg") or lowf.endswith(".png")) and signed:
            new_element = cl.Image(
                name=encoded_filename,
                url=link,
                display="inline"
            )
        else:
            new_element = cl.File(
                    name=encoded_filename,
                    url=link,
                    display="side" if signed else "inline",
                )
            #log.info(f"Added file elements: {encoded_filename} {link}")
        output_elements.append(new_element)

    return output_elements

