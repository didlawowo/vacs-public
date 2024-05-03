import os
from chainlit import make_async
import chainlit as cl
from sunholo.gcs.add_file import add_file_to_gcs
from sunholo.chunker.loaders import read_file_to_documents
from .config import lookup_config
from .log import log

def get_bucket_and_type(file_mime):
    chat_profile    = cl.user_session.get("chat_profile")
    config = lookup_config(chat_profile)
    upload_config = config.get("upload", {})
    buckets_config = upload_config.get("buckets", {})

    # Default/fallback bucket and type
    fallback_bucket = buckets_config.get("all")
    fallback_type = "other"

    # Iterate through buckets_config to find a match
    for mime_type, bucket_name in buckets_config.items():
        if mime_type in file_mime:
            return bucket_name, mime_type.split('/')[0]  # E.g., "image" for "image/png"

    # If no specific match found and "all" is allowed
    if fallback_bucket and "all" in upload_config.get("mime_types", []):
        return fallback_bucket, fallback_type

    return None, None

async_read_file_to_documents = make_async(read_file_to_documents)

# "run", "tool", "llm", "embedding", "retrieval", "rerank", "undefined"
@cl.step(name="Parsing document", type="retrieval")
async def process_docs_tool(file):
    docs = await async_read_file_to_documents(file, metadata={"type":"private_upload"})
    content = ""
    for doc in docs:
        content += doc.page_content

    log.info(f"Private document of length: {len(content)}")
    return content

@cl.step(name="Uploading document", type="retrieval")
async def process_uploads_tool(file, vector_name, message_content):
    chat_profile    = cl.user_session.get("chat_profile")
    bucket, file_type = get_bucket_and_type(file.mime)
    if not bucket:
        log.error(f"No bucket defined for file type {file.mime}")
        return None, None
    
    log.info(f"Uploading file {file}")
    file_url = add_file_to_gcs(file.path, 
                               vector_name=vector_name, 
                               bucket_name=bucket,
                               metadata={"type": "chainlit",
                                         "message": message_content,
                                         "chat_profile": chat_profile,
                                         "file_type": file_type},
                                bucket_filepath=f"{vector_name}/uploads/{file_type}/{os.path.basename(file.path)}")
    return file_url, file_type

async def process_uploads(message: cl.Message):
    
    chat_profile    = cl.user_session.get("chat_profile")
    settings        = cl.user_session.get("settings")
    private_upload  = settings.get("private_upload") if settings else None

    config = lookup_config(chat_profile)
    upload_config = config.get("upload")

    if not upload_config:
        return None
    

    # TODO: not implemented yet
    if settings and settings.get("personal_upload"):
        log.info("Personal upload for user")
        app_user        = cl.user_session.get("user")
        upload_vector_name = str(app_user.id)
        if upload_vector_name is None:
            log.warning(f"Could not assign a personal upload for user: {app_user}")
            upload_vector_name = config["name"]
    else:
        #TODO: the default for now
        upload_vector_name = config["name"]

    files_to_upload = []
    if "all" in upload_config.get("mime_types", []):
        files_to_upload.extend(message.elements)  # Include all files
    else:
        for upload_mime in upload_config.get("mime_types", []):
            files = [file for file in message.elements if upload_mime in file.mime]
            if files:
                files_to_upload.extend(files)
    
    if not files_to_upload:
        return None

    # Create a reply message for uploading
    msg = cl.Message(author=chat_profile, content="Uploading files...")
    await msg.send()

    if private_upload:
        private_docs = []
        for file in files_to_upload:
            log.info(f"Private upload for {file}")
            doc = await process_docs_tool(file.path)
            if doc:                
                private_docs.append(doc)
        cl.user_session.set("latest_private_uploads", private_docs)

        log.info("Created private docs string")
        return {"private_uploads": private_docs}
    
    log.info("Processing files to upload")
    file_urls_by_type = {}
    for file in files_to_upload:
        file_url, file_type = await process_uploads_tool(
                                            file, 
                                            vector_name=upload_vector_name, 
                                            message_content=message.content
                                        )
        if file_url and file_type:  # Ensure they are not None
            if file_type not in file_urls_by_type:
                file_urls_by_type[file_type] = []
            file_urls_by_type[file_type].append(file_url)
        else:
            msg.content = f"File type: {file_type} have not been configured to allow uploading so will not upload {file_url}."
            await msg.update()

    msg.content = f"Processed uploading [{len(files_to_upload)}] file(s)"

    image_urls = file_urls_by_type.get("image")
    if image_urls:
        img_url = image_urls[0]
        cl.user_session.set("latest_image_url", img_url)

    log.info(f"Uploaded file_urls_by_type:{file_urls_by_type}")

    return file_urls_by_type