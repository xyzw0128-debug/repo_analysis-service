import json
import time


class InputTooLargeError(Exception): ...
class ValidationFailureError(Exception): ...
class AnalysisFailedError(Exception): ...


class LLMClient:
    def __init__(self, provider: str, model: str, api_client, max_input_tokens: int = 60000):
        self.provider = provider
        self.model = model
        self.api_client = api_client
        self.max_input_tokens = max_input_tokens

    def _count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def analyze(self, system: str, user: str):
        tokens_in = self._count_tokens(system + user)
        if tokens_in > self.max_input_tokens:
            raise InputTooLargeError()
        if self.provider not in {"openai", "anthropic"}:
            raise ValueError("Unsupported provider")
        history = [{"role": "user", "content": user}]
        retry_count = 0
        start = time.time()
        last_err = None
        for attempt in range(3):
            try:
                raw = self.api_client.generate(provider=self.provider, model=self.model, system=system, messages=history, temperature=0.2, max_tokens=1000, timeout=30)
                parsed = json.loads(raw)
                if "summary" not in parsed:
                    raise ValidationFailureError("missing summary")
                return {"result": parsed, "usage": {"tokens_in": tokens_in, "tokens_out": self._count_tokens(raw), "latency_ms": int((time.time()-start)*1000), "retry_count": retry_count, "model": self.model}}
            except (TimeoutError, json.JSONDecodeError, ValidationFailureError) as e:
                last_err = e
                retry_count += 1
                if attempt < 2:
                    history.append({"role": "assistant", "content": str(e)})
                    history.append({"role": "user", "content": "Return valid JSON only."})
        raise AnalysisFailedError(str(last_err))
