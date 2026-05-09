"""
Tool translation from Codex Responses API format to Chat Completions format.
Handles: local_shell, web_search, custom, namespace, server-side tool dropping.
"""
import uuid
from typing import Any, Dict, List, Optional, Union


# ------------------------------------------------------------------ #
#  Server-side tools that only OpenAI can fulfill — silently drop
# ------------------------------------------------------------------ #
SERVER_SIDE_TOOLS = {
    "code_interpreter",
    "file_search",
    "image_generation",
    "computer_use_preview",
    "computer_use",
}

# Track warned tool types to avoid log spam
_warned_types: set = set()

# Canonical local_shell → shell function schema
LOCAL_SHELL_FN: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "shell",
        "description": "Execute a shell command on the local machine. Returns stdout, stderr and exit code.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": 'Argv array, e.g. ["ls", "-la"].',
                },
                "workdir": {
                    "type": "string",
                    "description": "Working directory (optional).",
                },
                "timeout_ms": {
                    "type": "number",
                    "description": "Timeout in milliseconds (optional, default 30000).",
                },
            },
            "required": ["command"],
        },
    },
}


def _new_id(prefix: str = "call") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


def translate_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Translate a list of Responses API tools to Chat Completions tools.
    Returns a flat list of Chat Completions tools, deduplicated by name.
    """
    result = []
    seen_names: set = set()
    for tool in tools:
        translated = _translate_one_tool(tool)
        if translated is None:
            continue
        items = translated if isinstance(translated, list) else [translated]
        for item in items:
            name = item.get("function", {}).get("name", "")
            if name and name in seen_names:
                continue  # skip duplicate
            if name:
                seen_names.add(name)
            result.append(item)
    return result


def _translate_one_tool(tool: Dict[str, Any]) -> Optional[Union[Dict, List[Dict]]]:
    t = tool.get("type", "")

    # 1. Standard function tool — pass through
    #    Handle both formats: {type:"function", function:{name:...}} and {type:"function", name:...}
    if t == "function":
        func = tool.get("function") or tool  # fallback to top-level if no "function" wrapper
        if not func.get("name"):
            return None
        fn: Dict[str, Any] = {
            "name": func["name"],
            "description": func.get("description", ""),
            "parameters": func.get("parameters", {"type": "object", "properties": {}}),
        }
        if func.get("strict") is not None:
            fn["strict"] = func["strict"]
        return {"type": "function", "function": fn}

    # 2. local_shell → shell function
    if t == "local_shell":
        return LOCAL_SHELL_FN

    # 3. web_search / web_search_preview → MiMo-style web_search
    #    Token-plan accounts don't have webSearchEnabled, so strip it to avoid 400
    if t in ("web_search", "web_search_preview"):
        return None  # silently drop — MiMo token-plan doesn't support web search

    # 4. custom tool → parameterless function
    if t == "custom":
        name = tool.get("name", "")
        if not name:
            return None
        desc = tool.get("description", "")
        fmt_type = (tool.get("format") or {}).get("type")
        if fmt_type:
            desc += f' (originally a "{fmt_type}"-format custom tool)'
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": desc.strip() or "",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Input text for the tool.",
                        },
                    },
                    "additionalProperties": True,
                },
            },
        }

    # 5. namespace — recurse and flatten
    if t == "namespace":
        nested = tool.get("tools", [])
        if not nested:
            return None
        result = []
        for inner in nested:
            r = _translate_one_tool(inner)
            if r is None:
                continue
            if isinstance(r, list):
                result.extend(r)
            else:
                result.append(r)
        return result if result else None

    # 6. Server-side tools — silently drop
    if t in SERVER_SIDE_TOOLS:
        return None

    # 7. Unknown — warn once per type
    if t not in _warned_types:
        _warned_types.add(t)
        print(f"[CodexBridge] Dropping unsupported tool type: {t}")
    return None


def translate_tool_choice(tc: Any) -> Any:
    """Translate Responses tool_choice to Chat Completions tool_choice."""
    if tc is None:
        return None
    if isinstance(tc, str):
        if tc in ("none", "auto", "required"):
            return tc
        return None
    if isinstance(tc, dict):
        tc_type = tc.get("type", "")
        if tc_type == "function":
            name = tc.get("function", {}).get("name") or tc.get("name", "")
            if name:
                return {"type": "function", "function": {"name": name}}
        if tc_type == "allowed_tools":
            return "auto"
        return "auto"
    return None
