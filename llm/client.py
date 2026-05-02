import json
import time
import tiktoken
from pydantic import ValidationError
from models.output import RepoAnalysisOutput


class InputTooLargeError(Exception):
    pass


class ValidationFailureError(Exception):
    pass


class AnalysisFailedError(Exception):
    pass


def _count_tokens(system: str, user: str) -> int:
    enc = tiktoken.get_encoding('cl100k_base')
    return len(enc.encode(system + '\n' + user))


def analyze_with_llm(provider: str, model: str, system: str, user: str, max_input_tokens: int, api_client):
    tokens_in = _count_tokens(system, user)
    if tokens_in > max_input_tokens:
        raise InputTooLargeError('Input exceeds token limit')
    if provider not in {'anthropic', 'openai'}:
        raise ValueError('Unsupported provider')

    messages = [{'role': 'user', 'content': user}]
    retry_count = 0
    start = time.time()
    last_error = None
    while retry_count <= 2:
        try:
            resp = api_client.chat(system=system, messages=messages, model=model, temperature=0.2, max_tokens=1000, timeout=30)
            text = resp['text']
            data = json.loads(text)
            validated = RepoAnalysisOutput.model_validate(data)
            latency_ms = int((time.time() - start) * 1000)
            return validated, {
                'tokens_in': tokens_in,
                'tokens_out': resp.get('tokens_out', 0),
                'latency_ms': latency_ms,
                'retry_count': retry_count,
                'model': model,
            }
        except (json.JSONDecodeError, ValidationError, TimeoutError) as exc:
            last_error = exc
            if retry_count >= 2:
                break
            messages.append({'role': 'assistant', 'content': getattr(resp, 'text', '') if 'resp' in locals() else ''})
            messages.append({'role': 'user', 'content': 'Your previous response failed JSON/schema validation. Return valid JSON only.'})
            retry_count += 1
            continue
        except Exception as exc:
            raise AnalysisFailedError('LLM call failed') from exc
    if isinstance(last_error, ValidationError):
        raise ValidationFailureError('Validation failed') from last_error
    raise AnalysisFailedError('Failed after retries') from last_error
