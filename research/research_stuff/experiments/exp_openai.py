import os

# Check for the OPENAI_API_KEY environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key:
    print("✅ OPENAI_API_KEY is present in the environment.")
    # You can optionally print the first few characters for confirmation (DON'T print the whole key!)
    # print(f"Key snippet: {openai_api_key[:5]}...")
else:
    print("❌ OPENAI_API_KEY is NOT present in the environment.")
    print("Please set the environment variable to your OpenAI API key.")

# Example of integrating this check before initializing the client (if you use the key explicitly)
# Note: The OpenAI client will generally look for this variable automatically.
# from openai import OpenAI
# if openai_api_key:
#     client = OpenAI(api_key=openai_api_key)
#     print("OpenAI client initialized.")
# else:
#     print("Cannot initialize OpenAI client without API key.")