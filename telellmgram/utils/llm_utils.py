"""Required functions and classes to work with llm"""
from dataclasses import dataclass
import openai


@dataclass
class LLMConfig:
    base_url = 'https://api.avalapis.ir/v1'
    api_key  = 'XXXX'
    model_name = "gpt-4o-mini"


LLM_CONFIG = LLMConfig()


def call_llm(prompt_text):
    openai.api_key = LLM_CONFIG.api_key
    openai.api_base = LLM_CONFIG.base_url
    model_name = LLM_CONFIG.model_name

    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt_text}],
            temperature=0.2,
            max_tokens=1000
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"
