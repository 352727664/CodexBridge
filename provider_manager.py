"""
Provider manager for handling multiple API providers (OpenAI & Anthropic formats).
"""
import json
from typing import Any, Dict, List, Optional

from providers import PROVIDER_CLASSES


class ProviderManager:
    """Manages multiple API providers via config.json."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.providers: Dict[str, Any] = {}
        self._load_providers()

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[CodexBridge] Config not found at {self.config_path}")
            print("[CodexBridge] Copy config.example.json to config.json and fill in your API keys.")
            return {"active_provider": "deepseek", "port": 8787, "providers": {}}

    def save_config(self) -> None:
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def _load_providers(self) -> None:
        for pid, pcfg in self.config.get("providers", {}).items():
            api_format = pcfg.get("api_format", "openai")
            cls = PROVIDER_CLASSES.get(api_format, PROVIDER_CLASSES["openai"])
            self.providers[pid] = cls(pid, pcfg)

    def get_active_provider(self) -> Optional[Any]:
        return self.providers.get(self.config.get("active_provider"))

    def get_provider(self, provider_id: str) -> Optional[Any]:
        return self.providers.get(provider_id)

    def set_active_provider(self, provider_id: str) -> bool:
        if provider_id in self.providers:
            self.config["active_provider"] = provider_id
            self.save_config()
            return True
        return False

    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": pid,
                "name": p.name,
                "api_format": getattr(p, "api_format", "openai"),
                "models": p.models,
                "has_reasoning": p.has_reasoning,
                "is_active": pid == self.config.get("active_provider"),
            }
            for pid, p in self.providers.items()
        ]

    def get_models(self) -> List[Dict[str, Any]]:
        models = []
        for pid, p in self.providers.items():
            for mid in p.models:
                models.append({
                    "id": mid,
                    "object": "model",
                    "owned_by": p.name,
                    "provider": pid,
                })
        return models