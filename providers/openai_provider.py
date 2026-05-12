"""
Translates between OpenAI Responses API (Codex) and Chat Completions API (providers).

Converts Responses API requests to Chat Completions format for providers like:
MiMo, DeepSeek, Qwen, Kimi, GLM, MiniMax, Baichuan, Yi, Doubao,
StepFun, SiliconFlow, OpenRouter, OpenAI, Groq, Together, Fireworks, etc.

Supports: reasoning, tool calls, multi-turn, tool translations,
structured output, image handling, web search, keepalive, error envelopes.
"""
import json
import time
import traceback
import uuid
from typing import Any, Dict, AsyncGenerator, List, Optional

import httpx

from .tool_translator import translate_tools, translate_tool_choice


# ------------------------------------------------------------------ #
#  ID generators
# ------------------------------------------------------------------ #
def _new_id(prefix: str = "resp") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


# ------------------------------------------------------------------ #
#  SSE helper
# ------------------------------------------------------------------ #
_seq_counter = 0

def _next_seq() -> int:
    global _seq_counter
    _seq_counter += 1
    return _seq_counter

def _sse(event: str, data: dict) -> str:
    payload = {"type": event, **data, "sequence_number": _next_seq()}
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _error_envelope(status: int, code: str, message: str) -> dict:
    type_map = {
        401: "authentication_error",
        429: "rate_limit_exceeded",
    }
    return {
        "error": {
            "type": type_map.get(status, "invalid_request_error") if status < 500 else "server_error",
            "code": code,
            "message": message,
            "status": status,
        }
    }


# ------------------------------------------------------------------ #
#  Image support detection
# ------------------------------------------------------------------ #
def _model_supports_images(model: str) -> bool:
    base = model.lower().replace("[1m]", "").replace("[128k]", "")
    if "omni" in base:
        return True
    if base == "mimo-v2.5":
        return True
    return False


# ------------------------------------------------------------------ #
#  Provider
# ------------------------------------------------------------------ #
class OpenAIProvider:
    """Universal OpenAI-compatible API provider."""

    def __init__(self, provider_id: str, config: Dict[str, Any]):
        self.id = provider_id
        self.name = config.get("name", provider_id.title())
        self.base_url = config.get("base_url", "")
        self.api_key = config.get("api_key", "")
        self.models = config.get("models", [])
        self.has_reasoning = config.get("has_reasoning", False)
        self.api_format = "openai"

    @property
    def default_model(self) -> str:
        return self.models[0] if self.models else "unknown"

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------ #
    #  Request conversion: Responses API → Chat Completions
    # ------------------------------------------------------------------ #
    def to_chat_completions(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an OpenAI Responses API request body to Chat Completions format."""
        messages: List[Dict[str, Any]] = []
        model = self.default_model
        supports_images = _model_supports_images(model)

        # --- instructions → system message ---
        instructions = body.get("instructions", "")
        if instructions:
            messages.append({"role": "system", "content": instructions})

        # --- input → messages ---
        input_data = body.get("input", [])
        if isinstance(input_data, str):
            messages.append({"role": "user", "content": input_data})
        elif isinstance(input_data, list):
            messages.extend(self._input_items_to_messages(input_data, supports_images))

        result: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        # --- max_output_tokens → max_completion_tokens ---
        max_tokens = body.get("max_output_tokens")
        if max_tokens:
            result["max_completion_tokens"] = max_tokens

        # --- tools ---
        if body.get("tools"):
            translated = translate_tools(body["tools"])
            if translated:
                result["tools"] = translated

        # --- tool_choice ---
        tc = translate_tool_choice(body.get("tool_choice"))
        if tc is not None:
            result["tool_choice"] = tc

        # --- passthrough parameters ---
        if body.get("parallel_tool_calls") is not None:
            result["parallel_tool_calls"] = body["parallel_tool_calls"]
        if body.get("temperature") is not None:
            result["temperature"] = body["temperature"]
        if body.get("top_p") is not None:
            result["top_p"] = body["top_p"]

        # --- MiMo: disable thinking mode to avoid reasoning_content requirement ---
        if "mimo" in model.lower():
            result["thinking"] = {"type": "disabled"}

        # --- stream ---
        if body.get("stream"):
            result["stream"] = True
            result["stream_options"] = {"include_usage": True}

        return result

    def _input_items_to_messages(
        self, items: List[Dict[str, Any]], supports_images: bool
    ) -> List[Dict[str, Any]]:
        """Convert Responses API input items to Chat messages with proper assembly."""
        messages: List[Dict[str, Any]] = []
        pending_reasoning: Optional[str] = None
        pending_tool_calls: List[Dict[str, Any]] = []
        pending_assistant_text: Optional[str] = None

        def flush_assistant():
            nonlocal pending_reasoning, pending_tool_calls, pending_assistant_text
            has_reasoning = pending_reasoning is not None
            has_tools = len(pending_tool_calls) > 0
            has_text = pending_assistant_text is not None

            if not has_reasoning and not has_tools and not has_text:
                return

            msg: Dict[str, Any] = {
                "role": "assistant",
                "content": pending_assistant_text or "",
            }
            if has_tools:
                msg["tool_calls"] = pending_tool_calls
            if has_reasoning:
                msg["reasoning_content"] = pending_reasoning
            messages.append(msg)

            pending_reasoning = None
            pending_tool_calls = []
            pending_assistant_text = None

        for item in items:
            item_type = item.get("type", "")
            role = item.get("role", "user")

            if item_type == "message":
                if role == "assistant":
                    content = self._parts_to_content(item.get("content", ""), supports_images)
                    pending_assistant_text = content if isinstance(content, str) else ""
                    flush_assistant()
                else:
                    flush_assistant()
                    messages.append(self._message_item_to_chat(item, supports_images))

            elif item_type == "reasoning":
                flush_assistant()
                summary = item.get("summary", [])
                text_parts = [s.get("text", "") for s in summary if s.get("type") == "summary_text"]
                pending_reasoning = "".join(text_parts)

            elif item_type == "function_call":
                pending_tool_calls.append({
                    "id": item.get("call_id", _new_id("call")),
                    "type": "function",
                    "function": {
                        "name": item.get("name", ""),
                        "arguments": item.get("arguments", "{}"),
                    },
                })

            elif item_type == "function_call_output":
                flush_assistant()
                messages.append({
                    "role": "tool",
                    "tool_call_id": item.get("call_id", ""),
                    "content": item.get("output", ""),
                })

        flush_assistant()
        return messages

    def _message_item_to_chat(
        self, item: Dict[str, Any], supports_images: bool
    ) -> Dict[str, Any]:
        role = item.get("role", "user")
        content = self._parts_to_content(item.get("content", ""), supports_images)
        return {"role": role, "content": content}

    def _parts_to_content(
        self, content: Any, supports_images: bool
    ) -> Any:
        """Convert Responses content parts to Chat Completions content."""
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return str(content) if content else ""

        out_parts: List[Dict[str, Any]] = []
        dropped_images = 0

        for part in content:
            if not isinstance(part, dict):
                continue
            ptype = part.get("type", "")

            if ptype in ("input_text", "output_text"):
                text = part.get("text", "")
                if isinstance(text, str) and len(text) > 0:
                    out_parts.append({"type": "text", "text": text})

            elif ptype == "input_image":
                if supports_images:
                    out_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": part.get("image_url", ""),
                            "detail": part.get("detail", "auto"),
                        },
                    })
                else:
                    dropped_images += 1

            elif ptype == "input_file":
                continue  # MiMo doesn't support file inputs

        if dropped_images > 0:
            out_parts.append({
                "type": "text",
                "text": f"[{dropped_images} image attachment{'s' if dropped_images > 1 else ''} omitted: model does not support image input]",
            })

        # Ensure image messages always have a text part
        has_image = any(p.get("type") == "image_url" for p in out_parts)
        has_text = any(p.get("type") == "text" for p in out_parts)
        if has_image and not has_text:
            out_parts.append({"type": "text", "text": " "})

        # Collapse pure text to string
        if out_parts and all(p.get("type") == "text" for p in out_parts):
            return "".join(p.get("text", "") for p in out_parts)

        if not out_parts:
            return ""

        return out_parts

    # ------------------------------------------------------------------ #
    #  Response conversion: Chat Completions → Responses API
    # ------------------------------------------------------------------ #
    def to_responses(self, data: Dict[str, Any], request_body: Optional[Dict] = None) -> Dict[str, Any]:
        """Convert a Chat Completions response back to Responses API format."""
        output: List[Dict[str, Any]] = []
        content = ""
        reasoning = ""

        if data.get("choices"):
            msg = data["choices"][0].get("message", {})
            content = msg.get("content", "") or ""
            reasoning = msg.get("reasoning_content", "") or ""

            # Handle tool_calls
            tool_calls = msg.get("tool_calls") or []
            for tc in tool_calls:
                if tc.get("type") == "function":
                    func = tc.get("function", {})
                    output.append({
                        "type": "function_call",
                        "id": _new_id("fc"),
                        "call_id": tc.get("id", _new_id("call")),
                        "name": func.get("name", ""),
                        "arguments": func.get("arguments", "{}"),
                        "status": "completed",
                    })

        # Add reasoning if present
        if reasoning and self.has_reasoning:
            output.insert(0, {
                "type": "reasoning",
                "id": _new_id("rs"),
                "summary": [{"type": "summary_text", "text": reasoning}],
                "encrypted_content": None,
                "status": "completed",
            })

        # Add text content
        if content:
            output.append({
                "type": "message",
                "id": _new_id("msg"),
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": content, "annotations": []}],
            })

        if not output:
            output.append({
                "type": "message",
                "id": _new_id("msg"),
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": "", "annotations": []}],
            })

        # Usage with details
        usage_raw = data.get("usage", {})
        usage = {
            "input_tokens": usage_raw.get("prompt_tokens", 0),
            "output_tokens": usage_raw.get("completion_tokens", 0),
            "total_tokens": usage_raw.get("total_tokens", 0),
        }
        prompt_details = usage_raw.get("prompt_tokens_details", {})
        if prompt_details and "cached_tokens" in prompt_details:
            usage["input_tokens_details"] = {"cached_tokens": prompt_details["cached_tokens"]}
        comp_details = usage_raw.get("completion_tokens_details", {})
        if comp_details and "reasoning_tokens" in comp_details:
            usage["output_tokens_details"] = {"reasoning_tokens": comp_details["reasoning_tokens"]}

        resp_id = _new_id("resp")

        # Build full response snapshot
        snapshot = {
            "id": resp_id,
            "object": "response",
            "created_at": int(time.time()),
            "status": "completed",
            "model": data.get("model", self.default_model),
            "output": output,
            "usage": usage,
            "parallel_tool_calls": (request_body or {}).get("parallel_tool_calls", True),
            "tool_choice": (request_body or {}).get("tool_choice", "auto"),
            "reasoning": {
                "effort": ((request_body or {}).get("reasoning") or {}).get("effort"),
                "summary": ((request_body or {}).get("reasoning") or {}).get("summary"),
            },
            "text": {
                "format": ((request_body or {}).get("text") or {}).get("format", {"type": "text"}),
            },
            "incomplete_details": None,
            "error": None,
            "metadata": (request_body or {}).get("metadata"),
            "previous_response_id": (request_body or {}).get("previous_response_id"),
            "instructions": (request_body or {}).get("instructions"),
            "temperature": (request_body or {}).get("temperature"),
            "top_p": (request_body or {}).get("top_p"),
            "max_output_tokens": (request_body or {}).get("max_output_tokens"),
            "tools": (request_body or {}).get("tools", []),
            "truncation": "disabled",
        }

        return snapshot

    # ------------------------------------------------------------------ #
    #  Streaming: Chat Completions SSE → Responses API SSE
    # ------------------------------------------------------------------ #
    async def stream(
        self,
        chat_req: Dict[str, Any],
        request_body: Optional[Dict] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream an OpenAI-compatible Chat Completions response
        re-framed as an OpenAI Responses API SSE stream.

        Strategy: wait for upstream 200 before opening SSE to client,
        so upstream errors map to clean HTTP errors.
        """
        global _seq_counter
        _seq_counter = 0

        model = self.default_model
        url = f"{self.base_url}/chat/completions"

        resp_id = _new_id("resp")
        created_at = int(time.time())
        reasoning_cfg = (request_body or {}).get("reasoning") or {}
        expose_reasoning = self.has_reasoning and reasoning_cfg.get("effort") != "none"

        # Stream state
        output_index = 0
        active_kind: Optional[str] = None  # "reasoning" | "message" | None
        active_item_id: Optional[str] = None
        active_buffer = ""
        tool_call_states: Dict[int, Dict[str, Any]] = {}
        final_output: List[Dict[str, Any]] = []
        finish_reason = None
        usage = {}

        def emit(event: str, data: dict):
            payload = {"type": event, **data, "sequence_number": _next_seq()}
            return f"event: {event}\ndata: {json.dumps(payload)}\n\n"

        def build_snapshot(status: str) -> dict:
            return {
                "id": resp_id,
                "object": "response",
                "created_at": created_at,
                "status": status,
                "model": model,
                "output": final_output,
                "usage": usage,
                "parallel_tool_calls": (request_body or {}).get("parallel_tool_calls", True),
                "tool_choice": (request_body or {}).get("tool_choice", "auto"),
                "reasoning": {
                    "effort": ((request_body or {}).get("reasoning") or {}).get("effort"),
                    "summary": ((request_body or {}).get("reasoning") or {}).get("summary"),
                },
                "text": {
                    "format": ((request_body or {}).get("text") or {}).get("format", {"type": "text"}),
                },
                "incomplete_details": None,
                "error": None,
                "metadata": (request_body or {}).get("metadata"),
                "previous_response_id": (request_body or {}).get("previous_response_id"),
                "instructions": (request_body or {}).get("instructions"),
                "temperature": (request_body or {}).get("temperature"),
                "top_p": (request_body or {}).get("top_p"),
                "max_output_tokens": (request_body or {}).get("max_output_tokens"),
                "tools": (request_body or {}).get("tools", []),
                "truncation": "disabled",
            }

        def finalize_active():
            nonlocal active_kind, active_item_id, active_buffer, output_index
            if active_kind is None:
                return

            item_id = active_item_id
            buf = active_buffer
            oi = output_index - 1

            if active_kind == "reasoning":
                yield emit("response.reasoning_summary_text.done", {
                    "item_id": item_id, "output_index": oi, "summary_index": 0, "text": buf,
                })
                yield emit("response.reasoning_summary_part.done", {
                    "item_id": item_id, "output_index": oi, "summary_index": 0,
                    "part": {"type": "summary_text", "text": buf},
                })
                final_item = {
                    "id": item_id, "type": "reasoning",
                    "summary": [{"type": "summary_text", "text": buf}],
                    "encrypted_content": None, "status": "completed",
                }
                final_output.append(final_item)
                yield emit("response.output_item.done", {
                    "output_index": oi, "item": final_item,
                })

            elif active_kind == "message":
                yield emit("response.output_text.done", {
                    "item_id": item_id, "output_index": oi, "content_index": 0, "text": buf,
                })
                yield emit("response.content_part.done", {
                    "item_id": item_id, "output_index": oi, "content_index": 0,
                    "part": {"type": "output_text", "text": buf, "annotations": []},
                })
                final_item = {
                    "id": item_id, "type": "message", "role": "assistant", "status": "completed",
                    "content": [{"type": "output_text", "text": buf, "annotations": []}],
                }
                final_output.append(final_item)
                yield emit("response.output_item.done", {
                    "output_index": oi, "item": final_item,
                })

            active_kind = None
            active_item_id = None
            active_buffer = ""

        def finalize_tool_calls():
            nonlocal output_index
            for idx in sorted(tool_call_states.keys()):
                tc = tool_call_states[idx]
                yield emit("response.function_call_arguments.done", {
                    "item_id": tc["item_id"], "output_index": tc["output_index"],
                    "arguments": tc["args_buffer"],
                })
                final_item = {
                    "id": tc["item_id"], "type": "function_call",
                    "call_id": tc["call_id"], "name": tc["name"],
                    "arguments": tc["args_buffer"], "status": "completed",
                }
                final_output.append(final_item)
                yield emit("response.output_item.done", {
                    "output_index": tc["output_index"], "item": final_item,
                })

        def open_reasoning():
            nonlocal active_kind, active_item_id, active_buffer, output_index
            # Close any active first
            for chunk in finalize_active():
                yield chunk
            active_kind = "reasoning"
            active_item_id = _new_id("rs")
            active_buffer = ""
            oi = output_index
            output_index += 1
            yield emit("response.output_item.added", {
                "output_index": oi,
                "item": {
                    "id": active_item_id, "type": "reasoning",
                    "summary": [], "encrypted_content": None, "status": "in_progress",
                },
            })
            yield emit("response.reasoning_summary_part.added", {
                "item_id": active_item_id, "output_index": oi, "summary_index": 0,
                "part": {"type": "summary_text", "text": ""},
            })

        def open_message():
            nonlocal active_kind, active_item_id, active_buffer, output_index
            for chunk in finalize_active():
                yield chunk
            active_kind = "message"
            active_item_id = _new_id("msg")
            active_buffer = ""
            oi = output_index
            output_index += 1
            yield emit("response.output_item.added", {
                "output_index": oi,
                "item": {
                    "id": active_item_id, "type": "message", "role": "assistant",
                    "status": "in_progress", "content": [],
                },
            })
            yield emit("response.content_part.added", {
                "item_id": active_item_id, "output_index": oi, "content_index": 0,
                "part": {"type": "output_text", "text": "", "annotations": []},
            })

        # --- Emit created + in_progress ---
        yield emit("response.created", {"response": build_snapshot("in_progress")})
        yield emit("response.in_progress", {"response": build_snapshot("in_progress")})

        # --- Stream processing ---
        import sys
        print(f"[CodexBridge] Streaming to upstream: {url}", file=sys.stderr, flush=True)
        http_client = httpx.AsyncClient(timeout=300, proxy=None)
        try:
            req = http_client.build_request("POST", url, json=chat_req, headers=self.get_headers())
            upstream_resp = await http_client.send(req, stream=True)
            print(f"[CodexBridge] Upstream status: {upstream_resp.status_code}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[CodexBridge] Upstream connection error: {e}", file=sys.stderr, flush=True)
            snapshot = build_snapshot("failed")
            snapshot["error"] = {"type": "upstream_error", "message": f"Failed to connect to upstream: {e}"}
            yield emit("response.failed", {"response": snapshot})
            return

        try:
            if upstream_resp.status_code != 200:
                err_body = (await upstream_resp.aread())[:500].decode(errors="replace")
                print(f"[CodexBridge] Upstream error {upstream_resp.status_code}: {err_body}", file=sys.stderr, flush=True)
                snapshot = build_snapshot("failed")
                snapshot["error"] = {"type": "upstream_error", "message": f"HTTP {upstream_resp.status_code}: {err_body}"}
                yield emit("response.failed", {"response": snapshot})
                return

            async for line in upstream_resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload_str = line[6:]
                if payload_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload_str)
                except json.JSONDecodeError:
                    continue

                # --- Usage ---
                if chunk.get("usage"):
                    u = chunk["usage"]
                    usage["input_tokens"] = u.get("prompt_tokens", 0)
                    usage["output_tokens"] = u.get("completion_tokens", 0)
                    usage["total_tokens"] = u.get("total_tokens", 0)
                    pt = u.get("prompt_tokens_details", {})
                    if pt and "cached_tokens" in pt:
                        usage["input_tokens_details"] = {"cached_tokens": pt["cached_tokens"]}
                    ct = u.get("completion_tokens_details", {})
                    if ct and "reasoning_tokens" in ct:
                        usage["output_tokens_details"] = {"reasoning_tokens": ct["reasoning_tokens"]}

                choices = chunk.get("choices")
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                finish = choices[0].get("finish_reason")

                # --- Reasoning (thinking) ---
                rc = delta.get("reasoning_content")
                if rc and expose_reasoning:
                    if active_kind != "reasoning":
                        for ch in open_reasoning():
                            yield ch
                    active_buffer += rc
                    yield emit("response.reasoning_summary_text.delta", {
                        "item_id": active_item_id,
                        "output_index": output_index - 1,
                        "summary_index": 0,
                        "delta": rc,
                    })

                # --- Text content ---
                c = delta.get("content")
                if c:
                    if active_kind != "message":
                        for ch in open_message():
                            yield ch
                    active_buffer += c
                    yield emit("response.output_text.delta", {
                        "item_id": active_item_id,
                        "output_index": output_index - 1,
                        "content_index": 0,
                        "delta": c,
                    })

                # --- Tool calls ---
                for tc_delta in (delta.get("tool_calls") or []):
                    tc_index = tc_delta.get("index", 0)
                    if tc_index not in tool_call_states:
                        for ch in finalize_active():
                            yield ch
                        item_id = _new_id("fc")
                        call_id = tc_delta.get("id", _new_id("call"))
                        tc_name = tc_delta.get("function", {}).get("name", "")
                        oi = output_index
                        output_index += 1
                        tool_call_states[tc_index] = {
                            "item_id": item_id,
                            "output_index": oi,
                            "call_id": call_id,
                            "name": tc_name,
                            "args_buffer": "",
                        }
                        yield emit("response.output_item.added", {
                            "output_index": oi,
                            "item": {
                                "id": item_id, "type": "function_call",
                                "call_id": call_id, "name": tc_name,
                                "arguments": "", "status": "in_progress",
                            },
                        })
                        yield emit("response.function_call_arguments.start", {
                            "output_index": oi, "item_id": item_id,
                        })

                    tc = tool_call_states[tc_index]
                    args_delta = tc_delta.get("function", {}).get("arguments", "")
                    if args_delta:
                        tc["args_buffer"] += args_delta
                        yield emit("response.function_call_arguments.delta", {
                            "item_id": tc["item_id"],
                            "output_index": tc["output_index"],
                            "delta": args_delta,
                        })

                if finish:
                    finish_reason = finish
        except Exception as e:
            snapshot = build_snapshot("failed")
            snapshot["error"] = {"type": "server_error", "message": str(e)}
            yield emit("response.failed", {"response": snapshot})
            return

        # --- Finalize all open items ---
        for chunk in finalize_active():
            yield chunk
        for chunk in finalize_tool_calls():
            yield chunk

        # --- response.completed with full snapshot ---
        snapshot = build_snapshot("completed")
        yield emit("response.completed", {"response": snapshot})
        print(f"[CodexBridge] Stream completed OK (resp_id={resp_id})", file=sys.stderr, flush=True)
