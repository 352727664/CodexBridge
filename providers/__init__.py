from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .tool_translator import translate_tools, translate_tool_choice

# Map api_format string -> provider class
PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

__all__ = [
    "OpenAIProvider",
    "AnthropicProvider",
    "PROVIDER_CLASSES",
    "translate_tools",
    "translate_tool_choice",
]
