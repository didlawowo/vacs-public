from sunholo.utils import load_config
from chainlit.input_widget import Select, Switch, Slider, TextInput
import os
from .log import log

def lookup_config(chat_profile):

    configs, _ = load_config("config/llm_config.yaml")
    for name, value in configs.items():
        value["name"] = name
        if value.get('display_name') == chat_profile:
            return value
        elif name == chat_profile:
            return value

def lookup_settings(chat_profile):
    config          = lookup_config(chat_profile)
    vector_name     = config.get("name")

    log.info(f"lookup settings for {chat_profile} vector_name: {vector_name}")
    if vector_name == "default":
        return None
    elif vector_name == "eduvac":
       return [
            TextInput(
               id="source_filters", 
               label="Search Syllabus", 
               initial="",
               tooltip="Look for syllabus documents",
               description="This field is used to find what context sources shall be returned for you to learn.  Separate with a comma (,) to do multiple keywords e.g. 'genai, education'.  You can specify individual documents by providing the whole path e.g. 'documents/2024/march/my_learning_material.pdf'"
            ),
            Switch(
              id="source_filters_and_or",
              label="Source File Path AND Mode",
              initial=False,
              tooltip="Switch to True to change search behaviour from OR to AND",
              description="Switch to True to change source filter behaviour from OR to AND. e.g. by default 'italy,germany' will return two sets of documents: one set with 'italy' in the file path and one set with 'germany' in the file path.  Setting to True will return one set of files, that have both 'italy' and 'germany' in the file path."
            ),
            Switch(
              id="private_upload",
              label="Only This Session Upload",
              initial=False,
              tooltip="Activate to only use documents within this session",
              description="By default documents uploaded will be added to the main database upload bucket.  Set to True so that documents uploaded will only be available this user session. Warning: this may be slower as document text will be processed in real-time, not batch.  Will break for big documents."
            ),          
       ]

# settings parsing
def convert_field(field):
  """
  Converts a field into a list, handling strings and comma-separated values.

  Args:
      field: The field value to convert.

  Returns:
      A list representation of the field value.
  """
  if isinstance(field, str):
    # If string, remove whitespace and split on commas
    entries = field.strip().split(",")
    parsed_fields = []
    for entry in entries:
       parsed_fields.append(entry.strip())
    return parsed_fields
  
  elif isinstance(field, list):
    # If already a list, return as-is
    parsed_fields = []
    for entry in field:
       parsed_fields.append = entry.strip()
    return parsed_fields
  else:
    # Handle unexpected data types by returning an empty list
    return []
  
def k_settings(settings):
    fast_vs_accurate = settings.get('fast_vs_accurate', "balanced")

    if fast_vs_accurate == "none":
        search_kwargs = {
            'k': 0,
            'fetch_k': 0
        }
    elif fast_vs_accurate == "fast":
        search_kwargs = {
            'k': 10,
            'fetch_k': 20
        }
    elif fast_vs_accurate == "balanced":
        search_kwargs = {
            'k': 50,
            'fetch_k': 100
        }
    elif fast_vs_accurate == "extensive":
        search_kwargs = {
            'k': 100,
            'fetch_k': 400
        }
    else:
       log.warning("did not get correct fast_vs_account setting")
       search_kwargs = {
            'k': 50,
            'fetch_k': 200
        }
       
    whole_document = settings.get('whole_document')

    if whole_document:
       if search_kwargs['k'] > 10:
          search_kwargs['k'] = 10
          search_kwargs['fetch_k'] = 100

    return search_kwargs