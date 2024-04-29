from sunholo.logging import setup_logging
from sunholo.components import get_llm_chat, get_embeddings

VECTOR_NAME = "eduvac"
TOKEN_INPUT_LIMIT = 180000*5
FAST_TOKEN_LIMIT = 180000*5 #(6 is too big)


log = setup_logging(VECTOR_NAME)

embeddings  = get_embeddings(VECTOR_NAME)
model       = get_llm_chat(VECTOR_NAME)
quick_model = get_llm_chat(VECTOR_NAME, model="claude-3-sonnet-20240229")


def log_count_chars_in_docs(docs, type=""):
    char_count = 0
    for doc in docs:
        char_count += len(doc.page_content)

    log.info(f"Found [{len(docs)}] {type} documents with total character count: [{char_count}]")
