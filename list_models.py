import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=api_key)

print('Available models that support generateContent:')
for m in genai.list_models():
    methods = m.supported_generation_methods
    if 'generateContent' in methods:
        print(f'  - {m.name}')
