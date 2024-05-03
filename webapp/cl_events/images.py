import chainlit as cl

from sunholo.gcs import construct_download_link
import re
from .log import log


async def add_images(msg):
 
    content = msg.content
    # Regular expression to find gs:// URLs 
    pattern = r'gs://[^ ]+\.(?:png|jpg|jpeg)'

    gs_matches = re.findall(pattern, content)
    if gs_matches:
        log.info("adding images to msg...{content}")
        # for each gs:// link that ends with .png or .jpg or .jpeg create a viewable URL
        image_signed_urls = []
        for gs_url in gs_matches:
             link, encoded_filename, signed  = construct_download_link(gs_url)
             image_signed_urls.append({"original": gs_url,
                                       "link": link,
                                        "name": encoded_filename, 
                                        "signed": signed})
        
        # Replace each original gs:// URL with the signed URL in the markdown format
        for image_url in image_signed_urls:
            log.info(f"adding image url: {image_url}")
            if image_url.get('link'):
                name = image_url["name"]
                link = image_url["link"]
                signed_url_name = name
                original = image_url['original']
                log.info(f"image replace: {original} with {signed_url_name}")
                content = content.replace(original, signed_url_name)
                msg.content = content

                element = cl.Image(
                    name=name,
                    url=link,
                    display="inline"
                )
                if hasattr(msg, 'elements'):
                    msg.elements.append(element)
                else:
                    msg.elements = [element]
                
                await msg.update()                             
