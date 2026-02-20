from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from settings import *
from prompts import *

def process_message(from_name, text):
    print(f'Processing message from {from_name}: {text}')

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        openai_api_key = OPENAI_API_KEY)

    chain = main_prompt | llm

    response = chain.invoke({"user_name": from_name, "user_input": text})

    return response.content
