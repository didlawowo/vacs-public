from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda, RunnableBranch
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.output_parsers import StrOutputParser

from typing import Optional, List
from operator import itemgetter

from .parsers import (
    format_docs, 
    format_chat_history, 
    format_chat_summary, 
    )

from .prompts import (
    prompt,
    summary_prompt,
)

from .utils import model, quick_model
from .retriever import get_retriever

class ChatEntry(BaseModel):
    name: str
    content: str

# if no summary needs to be generated from chat history (<1000), just passes through
# if summary can be created, creates summary and sends it to the prompt , 
summary_branch = RunnableBranch(
    # there is no summary to be created
    (lambda x: x.get("chat_summary")=="No summary", RunnablePassthrough()),
    # a summary is created from the x["chat_history"] key
    (summary_prompt | quick_model | StrOutputParser())
)

# these are all strings ready for the prompt
_inputs = RunnableParallel({
        "metadata": RunnableLambda(format_chat_history) | RunnableLambda(get_retriever) | RunnableLambda(format_docs),
        "question": itemgetter("question"),
        "chat_history": RunnableLambda(format_chat_history) | itemgetter("chat_history"),
        "chat_summary": RunnableLambda(format_chat_summary) | summary_branch | itemgetter("chat_summary"),
    })

# outputs the string for 'answer'
chain_qa = _inputs | prompt | model | StrOutputParser()

class Question(BaseModel):
    question: str
    #{"human": "How's the weather?", "ai": "It's sunny."},
    chat_history:   Optional[List[ChatEntry]] = []
    source_filters: Optional[List[str]] = []
    private_docs:   Optional[List[str]] = []
    source_filters_and_or: Optional[bool] = False

# return only content and sources in answer 
chain = chain_qa.with_types(input_type=Question)
