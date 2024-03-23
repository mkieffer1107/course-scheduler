import os
import json
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatCohere
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# map provider to langchain ChatModel
chat = {
    "groq": ChatGroq,
    "openai": ChatOpenAI,
    "anthropic": ChatAnthropic,
    "google": ChatGoogleGenerativeAI,
    "cohere": ChatCohere
}

def get_llm(provider: str, model: str, temperature: int, max_tokens: int, path: str = ".", stream: bool = False) -> BaseChatModel:
    """Returns a prepared langchain ChatModel"""
    print("Getting LLM API")
    provider = provider.lower()
    model = model.lower()

    # load the valid models 
    filepath = os.path.join(path, "providers.json")
    with open(filepath, "r") as file:
        providers = json.load(file)

    if provider in providers:
        # check that the model is valid
        if model in providers[provider]["models"]:
            # save the correct langchain ChatModel
            LLM = chat[provider]
        else:
            # invalid model
            valid_models_str = ", ".join(providers[provider]["models"])
            raise Exception(f"Invalid model: '{model}'. Valid models for provider {provider} are: {valid_models_str}")
    else:
        # invalid provider
        valid_providers_str = ", ".join(providers.keys())
        raise Exception(f"Invalid provider: '{provider}'. Valid providers are: {valid_providers_str}")
    # return LLM(model=model, temperature=temperature, max_tokens=max_tokens, streaming=stream, callbacks=[StreamingStdOutCallbackHandler()])
    return LLM(model=model, temperature=temperature, max_tokens=max_tokens, callbacks=[StreamingStdOutCallbackHandler()])