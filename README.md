# litellm-orogen-provider

LiteLLM provider plugin routing through the Orogen gateway. **Strategic acquisition channel** — any LiteLLM user can target the network with one line of config.

## Install

```bash
uv add litellm-orogen-provider
# or
pip install litellm-orogen-provider
```

## Configure

### Via LiteLLM `config.yaml`

```yaml
model_list:
  - model_name: llama-3.1-70b
    litellm_params:
      model: useful/llama-3.1-70b-instruct
      api_base: https://gateway.orogen.network/v1
      api_key: os.environ/OROGEN_API_KEY
```

### Via Python

```python
import litellm
response = litellm.completion(
    model="useful/llama-3.1-70b-instruct",
    messages=[{"role": "user", "content": "hi"}],
    api_base="https://gateway.orogen.network/v1",
    api_key="orog_...",
)
```

## Status

LiteLLM does not yet expose a stable provider-plugin API. This package implements the request/response shaping; full plugin registration is a stub for when that API ships. In the meantime, the `api_base` + `api_key` config above works because our gateway is OpenAI-compatible.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check
```
