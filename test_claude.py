
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("ERROR: API key not found in .env")
else:
    try:
        client = Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=60,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with: Hello! Claude API is working."
                }
            ],
        )

        print("SUCCESS: Claude API responded!")
        print(response.content[0].text)

    except Exception as error:
        print("API request failed.")
        print(type(error).__name__)
        print(str(error)[:500])
