import os
import json
from abc import ABC, abstractmethod

class AIService(ABC):
    @abstractmethod
    def get_response(self, user_input, system_prompt):
        pass

class OpenAIService(AIService):
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise Exception("OpenAI module not found. Please install the 'openai' package.")

    def get_response(self, user_input, system_prompt):
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0
            )
            return completion.choices[0].message.content
        except Exception as e:
            return json.dumps({"content": f"Error calling OpenAI API: {str(e)}", "query": ""})

class GeminiService(AIService):
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        except ImportError:
            raise Exception("Google Generative AI module not found. Please install 'google-generativeai'.")

    def get_response(self, user_input, system_prompt):
        try:
            # Gemini doesn't separate system prompt exactly like OpenAI in the simplest API, 
            # but we can prepend it or use the system_instruction if available in newer versions.
            # For robustness, we'll prepend the system prompt context.
            combined_prompt = f"{system_prompt}\n\nUser Request: {user_input}"
            
            response = self.model.generate_content(combined_prompt)
            return response.text
        except Exception as e:
            return json.dumps({"content": f"Error calling Gemini API: {str(e)}", "query": ""})

class MockService(AIService):
    def get_response(self, user_input, system_prompt):
        if "users" in user_input.lower():
            return json.dumps({
                "content": "Selecting all records from the generic users table.",
                "query": "SELECT * FROM users ORDER BY id DESC;"
            })
        else:
            return json.dumps({
                "content": "I received your request but I am running in MOCK mode.",
                "query": ""
            })

class AIServiceFactory:
    @staticmethod
    def get_service():
        provider = os.getenv("AI_PROVIDER", "openai").lower()
        
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                return OpenAIService(api_key)
        
        elif provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                return GeminiService(api_key)
        
        # Default to Mock if no keys or provider not recognized
        print(f"Warning: defaulting to MockService. Provider: {provider}")
        return MockService()
