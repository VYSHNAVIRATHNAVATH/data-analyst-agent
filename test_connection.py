# from utils.llm_client import chat

# messages = [
#     {"role": "user", "content": "Reply with exactly: CONNECTION OK"}
# ]

# response = chat(messages)
# print(response.choices[0].message.content)

from utils.llm_client import chat

response = chat([{"role": "user", "content": "Reply with: WORKING"}])
print(response.choices[0].message.content)