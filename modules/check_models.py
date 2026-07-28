from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

print("利用可能なモデル一覧")
print("-" * 50)

for model in client.models.list():
    print(model.name)