"""
Anthropic Messages API provider — fully compliant with OpenAI Responses API.
Handles: reasoning (thinking), tool calls, multi-turn with tool_result,
proper SSE event sequence, error envelopes.
"""
import json
import time
import uuid
from typing import Any, Dict, AsyncGenerator, List, Optional
import httpx


def _new_id(prefix: str = "resp") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"

_seq_counter = 0

def _next_seq() -> int:
    global _seq_counter
    _seq_counter += 1
    return _seq_counter


def _sse(event: str, data: dict) -> str:
    payload = {"type": event, **data, "sequence_number": _next_seq()}
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _error_envelope(status: int, code: str, message: str) -> dict:
    type_map = {401: "authentication_error", 429: "rate_limit_exceeded"}
    return {
        "error": {
            "type": type_map.get(status, "invalid_request_error") if status < 500 else "server_error",
            "code": code,
            "message": message,
            "status": status,
        }
    }


class AnthropicProvider:

    def __init__(self, provider_id: str, config: Dict[str, Any]):
        self.id = provider_id
        self.name = config.get("name", provider_id.title())
        self.base_url = config.get("base_url", "https://api.anthropic.com")
        self.api_key = config.get("api_key", "")
        self.models = config.get("models", [])
        self.has_reasoning = config.get("has_reasoning", True)
        self.api_format = "anthropic"

    @property
    def default_model(self) -> str:
        return self.models[0] if self.models else "claude-sonnet-4-20250514"

    def get_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def to_anthropic_request(self, body: Dict[str, Any]) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = []
        system_parts: List[str] = []

        instructions = body.get("instructions", "")
        if instructions:
            system_parts.append(instructions)

        input_data = body.get("input", [])
        if isinstance(input_data, str):
            messages.append({"role": "user", "content": input_data})
        elif isinstance(input_data, list):
            for item in input_data:
                item_type = item.get("type", "")
                role = item.get("role", "user")

                if item_type == "function_call_output":
                    messages.append({
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": item.get("call_id", ""), "content": item.get("output", "")}],
                    })
                    continue

                if item_type == "function_call":
                    msgs_input = {}
                    args = item.get("arguments", "{}")
                    try:
                        msgs_input = json.loads(args) if args else {}
                    except json.JSONDecodeError:
                        msgs_input = {"input": args}
                    messages.append({
                        "role": "assistant",
                        "content": [{"type": "tool_use", "id": item.get("call_id", _new_id("toolu")), "name": item.get("name", ""), "input": msgs_input}],
                    })
                    continue

                content = item.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "input_text":
                            parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            parts.append(block)
                    content = "\n".join(parts)

                if role == "system":
                    system_parts.append(content)
                else:
                    messages.append({"role": role, "content": content})

        result: Dict[str, Any] = {
            "model": body.get("model", self.default_model),
            "max_tokens": body.get("max_output_tokens", 4096),
            "messages": messages,
        }

        if system_parts:
            result["system"] = "\n\n".join(system_parts)

        if body.get("tools"):
            at = []
            for tool in body["tools"]:
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    at.append({
                        "type": "function",
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                    })
            if at:
                result["tools"] = at

        tc = body.get("tool_choice")
        if tc is not None:
            if isinstance(tc, str):
                if tc == "auto":
                    result["tool_choice"] = {"type": "auto"}
                elif tc == "required":
                    result["tool_choice"] = {"type": "any"}
            elif isinstance(tc, dict) and tc.get("type") == "function" and tc.get("name"):
                result["tool_choice"] = {"type": "tool", "name": tc["name"]}

        if body.get("stream"):
            result["stream"] = True

        return result

    def to_responses(self, data: Dict[str, Any], request_body: Optional[Dict] = None) -> Dict[str, Any]:
        output: List[Dict[str, Any]] = []
        reasoning = ""
        content = ""

        for block in data.get("content", []):
            if block.get("type") == "thinking":
                reasoning += block.get("thinking", "")
            elif block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                output.append({
                    "type": "function_call", "id": _new_id("fc"),
                    "call_id": block.get("id", _new_id("call")),
                    "name": block.get("name", ""),
                    "arguments": json.dumps(block.get("input", {})),
                    "status": "completed",
                })

        if reasoning and self.has_reasoning:
            output.insert(0, {
                "type": "reasoning", "id": _new_id("rs"),
                "summary": [{"type": "summary_text", "text": reasoning}],
                "encrypted_content": None, "status": "completed",
            })
        if content:
            output.append({
                "type": "message", "id": _new_id("msg"),
                "role": "assistant", "status": "completed",
                "content": [{"type": "output_text", "text": content, "annotations": []}],
            })
        if not output:
            output.append({
                "type": "message", "id": _new_id("msg"),
                "role": "assistant", "status": "completed",
                "content": [{"type": "output_text", "text": "", "annotations": []}],
            })

        usage_raw = data.get("usage", {})
        input_t = usage_raw.get("input_tokens", 0)
        output_t = usage_raw.get("output_tokens", 0)
        usage = {
            "input_tokens": input_t,
            "output_tokens": output_t,
            "total_tokens": input_t + output_t,
        }

        resp_id = _new_id("resp")
        rb = request_body or {}
        return {
            "id": resp_id, "object": "response", "created_at": int(time.time()),
            "status": "completed", "model": data.get("model", self.default_model),
            "output": output, "usage": usage,
            "parallel_tool_calls": rb.get("parallel_tool_calls", True),
            "tool_choice": rb.get("tool_choice", "auto"),
            "reasoning": {"effort": rb.get("reasoning", {}).get("effort"), "summary": rb.get("reasoning", {}).get("summary")},
            "text": {"format": rb.get("text", {}).get("format", {"type": "text"})},
            "incomplete_details": None, "error": None,
            "metadata": rb.get("metadata"), "previous_response_id": rb.get("previous_response_id"),
            "instructions": rb.get("instructions"), "temperature": rb.get("temperature"),
            "top_p": rb.get("top_p"), "max_output_tokens": rb.get("max_output_tokens"),
            "tools": rb.get("tools", []), "truncation": "disabled",
        }

    async def stream(self, anthropic_req: Dict[str, Any], request_body: Optional[Dict] = None) -> AsyncGenerator[str, None]:
        global _seq_counter
        _seq_counter = 0

        resp_id = _new_id("resp")
        created_at = int(time.time())
        expose_reasoning = self.has_reasoning and (request_body or {}).get("reasoning", {}).get("effort") != "none"

        output_index = 0
        active_kind: Optional[str] = None
        active_item_id: Optional[str] = None
        active_buffer = ""
        tool_blocks: Dict[str, Dict[str, Any]] = {}
        current_block_id = None
        current_block_type = None
        final_output: List[Dict[str, Any]] = []
        usage: Dict[str, Any] = {}

        model = anthropic_req.get("model", self.default_model)
        url = f"{self.base_url}/v1/messages"

        def emit(event: str, data: dict) -> str:
            payload = {"type": event, **data, "sequence_number": _next_seq()}
            return f"event: {event}\ndata: {json.dumps(payload)}\n\n"

        def build_snapshot(status: str) -> dict:
            rb = request_body or {}
            return {
                "id": resp_id, "object": "response", "created_at": created_at,
                "status": status, "model": model, "output": final_output, "usage": usage,
                "parallel_tool_calls": rb.get("parallel_tool_calls", True),
                "tool_choice": rb.get("tool_choice", "auto"),
                "reasoning": {"effort": rb.get("reasoning", {}).get("effort"), "summary": rb.get("reasoning", {}).get("summary")},
                "text": {"format": rb.get("text", {}).get("format", {"type": "text"})},
                "incomplete_details": None, "error": None,
                "metadata": rb.get("metadata"), "previous_response_id": rb.get("previous_response_id"),
                "instructions": rb.get("instructions"), "temperature": rb.get("temperature"),
                "top_p": rb.get("top_p"), "max_output_tokens": rb.get("max_output_tokens"),
                "tools": rb.get("tools", []), "truncation": "disabled",
            }

        def finalize_active():
            nonlocal active_kind, active_item_id, active_buffer, output_index
            if active_kind is None:
                return
            item_id = active_item_id
            buf = active_buffer
            oi = output_index - 1
            if active_kind == "reasoning":
                yield emit("response.reasoning_summary_text.done", {"item_id": item_id, "output_index": oi, "summary_index": 0, "text": buf})
                yield emit("response.reasoning_summary_part.done", {"item_id": item_id, "output_index": oi, "summary_index": 0, "part": {"type": "summary_text", "text": buf}})
                fi = {"id": item_id, "type": "reasoning", "summary": [{"type": "summary_text", "text": buf}], "encrypted_content": None, "status": "completed"}
                final_output.append(fi)
                yield emit("response.output_item.done", {"output_index": oi, "item": fi})
            elif active_kind == "message":
                yield emit("response.output_text.done", {"item_id": item_id, "output_index": oi, "content_index": 0, "text": buf})
                yield emit("response.content_part.done", {"item_id": item_id, "output_index": oi, "content_index": 0, "part": {"type": "output_text", "text": buf, "annotations": []}})
                fi = {"id": item_id, "type": "message", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "text": buf, "annotations": []}]}
                final_output.append(fi)
                yield emit("response.output_item.done", {"output_index": oi, "item": fi})
            active_kind = None
            active_item_id = None
            active_buffer = ""

        def open_reasoning():
            nonlocal active_kind, active_item_id, active_buffer, output_index
            for c in finalize_active(): yield c
            active_kind = "reasoning"
            active_item_id = _new_id("rs")
            active_buffer = ""
            oi = output_index; output_index += 1
            yield emit("response.output_item.added", {"output_index": oi, "item": {"id": active_item_id, "type": "reasoning", "summary": [], "encrypted_content": None, "status": "in_progress"}})
            yield emit("response.reasoning_summary_part.added", {"item_id": active_item_id, "output_index": oi, "summary_index": 0, "part": {"type": "summary_text", "text": ""}})

        def open_message():
            nonlocal active_kind, active_item_id, active_buffer, output_index
            for c in finalize_active(): yield c
            active_kind = "message"
            active_item_id = _new_id("msg")
            active_buffer = ""
            oi = output_index; output_index += 1
            yield emit("response.output_item.added", {"output_index": oi, "item": {"id": active_item_id, "type": "message", "role": "assistant", "status": "in_progress", "content": []}})
            yield emit("response.content_part.added", {"item_id": active_item_id, "output_index": oi, "content_index": 0, "part": {"type": "output_text", "text": "", "annotations": []}})

        # Emit created + in_progress
        yield emit("response.created", {"response": build_snapshot("in_progress")})
        yield emit("response.in_progress", {"response": build_snapshot("in_progress")})

        try:
            async with httpx.AsyncClient(timeout=300, proxy=None) as client:
                upstream_resp = await client.post(url, json=anthropic_req, headers=self.get_headers())

                if upstream_resp.status_code != 200:
                    err_body = upstream_resp.text[:500]
                    status = upstream_resp.status_code
                    snap = build_snapshot("failed")
                    snap["error"] = {"type": "upstream_error", "message": f"HTTP {status}: {err_body}"}
                    yield emit("response.failed", {"response": snap})
                    return

                event_type = ""
                async for line in upstream_resp.aiter_lines():
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                        continue
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    if event_type == "message_start":
                        msg = data.get("message", {})
                        if msg.get("usage"):
                            u = msg["usage"]
                            usage["input_tokens"] = u.get("input_tokens", 0)
                            usage["output_tokens"] = u.get("output_tokens", 0)
                            usage["total_tokens"] = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

                    elif event_type == "content_block_start":
                        block = data.get("content_block", {})
                        bt = block.get("type", "")
                        if bt == "thinking":
                            if not expose_reasoning:
                                continue
                            if active_kind != "reasoning":
                                for c in open_reasoning(): yield c
                        elif bt == "text":
                            if active_kind != "message":
                                for c in open_message(): yield c
                        elif bt == "tool_use":
                            for c in finalize_active(): yield c
                            tid = block.get("id", _new_id("toolu"))
                            tname = block.get("name", "")
                            oid = output_index; output_index += 1
                            fc_id = _new_id("fc")
                            tool_blocks[tid] = {"oid": oid, "id": fc_id, "call_id": tid, "name": tname, "args": ""}
                            current_block_id = tid
                            current_block_type = "tool_use"
                            yield emit("response.output_item.added", {"output_index": oid, "item": {"id": fc_id, "type": "function_call", "call_id": tid, "name": tname, "arguments": "", "status": "in_progress"}})
                            yield emit("response.function_call_arguments.start", {"output_index": oid, "item_id": fc_id})

                    elif event_type == "content_block_delta":
                        delta = data.get("delta", {})
                        dt = delta.get("type", "")
                        if dt == "thinking_delta" and expose_reasoning:
                            t = delta.get("thinking", "")
                            if t:
                                active_buffer += t
                                yield emit("response.reasoning_summary_text.delta", {"item_id": active_item_id, "output_index": output_index - 1, "summary_index": 0, "delta": t})
                        elif dt == "text_delta":
                            t = delta.get("text", "")
                            if t:
                                active_buffer += t
                                yield emit("response.output_text.delta", {"item_id": active_item_id, "output_index": output_index - 1, "content_index": 0, "delta": t})
                        elif dt == "input_json_delta":
                            pj = delta.get("partial_json", "")
                            if pj and current_block_id and current_block_id in tool_blocks:
                                tc = tool_blocks[current_block_id]
                                tc["args"] += pj
                                yield emit("response.function_call_arguments.delta", {"output_index": tc["oid"], "item_id": tc["id"], "delta": pj})

                    elif event_type == "content_block_stop":
                        if current_block_type == "tool_use" and current_block_id and current_block_id in tool_blocks:
                            tc = tool_blocks[current_block_id]
                            yield emit("response.function_call_arguments.done", {"output_index": tc["oid"], "arguments": tc["args"]})
                            fi = {"id": tc["id"], "type": "function_call", "call_id": tc["call_id"], "name": tc["name"], "arguments": tc["args"], "status": "completed"}
                            final_output.append(fi)
                            yield emit("response.output_item.done", {"output_index": tc["oid"], "item": fi})
                            output_index = tc["oid"] + 1
                            current_block_id = None
                            current_block_type = None

                    elif event_type == "message_delta":
                        delta = data.get("delta", {})
                        if delta.get("stop_reason"):
                            pass
                        if delta.get("usage"):
                            u = delta["usage"]
                            usage["output_tokens"] = u.get("output_tokens", usage.get("output_tokens", 0))
                            usage["total_tokens"] = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

        except Exception as e:
            print(f"[CodexBridge] Stream error ({self.id}): {e}")
            snap = build_snapshot("failed")
            snap["error"] = {"type": "server_error", "message": str(e)}
            yield emit("response.failed", {"response": snap})
            return

        for c in finalize_active(): yield c
        yield emit("response.completed", {"response": build_snapshot("completed")})
