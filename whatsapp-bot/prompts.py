from langchain_core.prompts import PromptTemplate

main_prompt = PromptTemplate(
    input_variables=["user_name", "user_input"],
    template="""
You're a kind assistant, say hello to the user.
Username:
'''
{user_name}
'''
User request:
'''
{user_input}
'''
    """
)