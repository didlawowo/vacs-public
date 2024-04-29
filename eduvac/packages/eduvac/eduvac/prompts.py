import datetime

from langchain.prompts import ChatPromptTemplate, PromptTemplate
from sunholo.langfuse.prompts import load_prompt_from_yaml

backup_yaml = 'packages/eduvac/eduvac/prompt_template.yaml'

intro_template = load_prompt_from_yaml("intro", prefix="eduvac", file_path=backup_yaml)

# Format the date into the prompt
the_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')
intro = intro_template.format(the_date=the_date)

template = load_prompt_from_yaml("template", prefix="eduvac", file_path=backup_yaml)

full_template = intro + template
prompt = ChatPromptTemplate.from_template(full_template, file_path=backup_yaml)

# chat history
chat_summary = load_prompt_from_yaml("chat_summary", prefix="eduvac", file_path=backup_yaml)
summary_prompt = ChatPromptTemplate.from_template(chat_summary)

summary_question_template = load_prompt_from_yaml('summarise_known_question', prefix="eduvac", file_path=backup_yaml)
summary_question_prompt = PromptTemplate.from_template(summary_question_template)