"""LiteLLM provider plugin for the Orogen.

Usage (litellm config.yaml):
    model_list:
      - model_name: useful/llama-3.1-70b
        litellm_params:
          model: useful/llama-3.1-70b-instruct
          api_base: https://gateway.orogen.network/v1
          api_key: os.environ/OROGEN_API_KEY

Then call via standard LiteLLM:
    import litellm
    response = litellm.completion(
        model="useful/llama-3.1-70b",
        messages=[{"role": "user", "content": "hi"}],
    )
"""

from litellm_orogen_provider.provider import OrogenProvider, register

__all__ = ["OrogenProvider", "register"]
__version__ = "0.1.0"
