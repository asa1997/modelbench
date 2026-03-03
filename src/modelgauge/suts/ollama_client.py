import time
from typing import List, Optional

import requests
from airrlogger.log_config import get_logger
from pydantic import BaseModel
from requests.adapters import HTTPAdapter, Retry

from modelgauge.auth.ollama_key import OllamaApiKey, OllamaBaseUrl
from modelgauge.general import APIException
from modelgauge.model_options import ModelOptions, TokenProbability, TopTokens
from modelgauge.prompt import ChatPrompt, ChatRole, TextPrompt
from modelgauge.prompt_formatting import format_chat
from modelgauge.secret_values import InjectSecret
from modelgauge.sut import PromptResponseSUT, SUTResponse
from modelgauge.sut_capabilities import AcceptsChatPrompt, AcceptsTextPrompt, ProducesPerTokenLogProbabilities
from modelgauge.sut_decorator import modelgauge_sut
from modelgauge.sut_registry import SUTS

logger = get_logger(__name__)

_SYSTEM_ROLE = "system"
_USER_ROLE = "user"
_ASSISTANT_ROLE = "assistant"

_ROLE_MAP = {
    ChatRole.user: _USER_ROLE,
    ChatRole.sut: _ASSISTANT_ROLE,
    ChatRole.system: _SYSTEM_ROLE,
}

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


def _retrying_request(url, headers, json_payload, method):
    """HTTP request with retry behavior."""
    session = requests.Session()
    retries = Retry(
        total=10,
        backoff_factor=1,
        status_forcelist=[
            408,  # Request Timeout
            429,  # Too Many Requests
        ]
        + list(range(500, 599)),  # Add all 5XX.
        allowed_methods=[method],
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    
    if method == "POST":
        call = session.post
    elif method == "GET":
        call = session.get
    else:
        raise ValueError(f"Invalid HTTP method: {method}")
    
    response = None
    try:
        response = call(url, headers=headers, json=json_payload, timeout=300)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.error(f"Failed on request {url} {headers} {json_payload}", exc_info=e)
        raise Exception(
            f"Exception calling {url} with {json_payload}. Response {response.text if response else response}"
        ) from e


class OllamaCompletionsRequest(BaseModel):
    """Request for Ollama's /api/generate endpoint."""
    model: str
    prompt: str
    stream: bool = False
    options: Optional[dict] = None
    # Options can include: temperature, top_p, top_k, num_predict (max_tokens), stop, etc.


class OllamaCompletionsResponse(BaseModel):
    """Response from Ollama's /api/generate endpoint."""
    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


@modelgauge_sut(
    capabilities=[
        AcceptsTextPrompt,
        AcceptsChatPrompt,
    ]
)
class OllamaCompletionsSUT(PromptResponseSUT):
    """
    SUT for Ollama completions API.
    Ollama runs locally and provides an API compatible with various models.
    """

    def __init__(
        self,
        uid: str,
        model: str,
        api_key: Optional[OllamaApiKey] = None,
        base_url: Optional[OllamaBaseUrl] = None,
    ):
        super().__init__(uid)
        self.model = model
        self.api_key = api_key.value if api_key else None
        
        # Handle base_url: check if it's an object with value, or use default
        if base_url and base_url.value:
            self.base_url = base_url.value
        else:
            self.base_url = DEFAULT_OLLAMA_BASE_URL
        
        # Ensure base_url doesn't end with /
        self.base_url = self.base_url.rstrip("/")
        self._api_endpoint = f"{self.base_url}/api/generate"

    def translate_text_prompt(self, prompt: TextPrompt, options: ModelOptions) -> OllamaCompletionsRequest:
        return self._translate_request(prompt.text, options)

    def translate_chat_prompt(self, prompt: ChatPrompt, options: ModelOptions) -> OllamaCompletionsRequest:
        return self._translate_request(format_chat(prompt, user_role=_USER_ROLE, sut_role=_ASSISTANT_ROLE), options)

    def _translate_request(self, text: str, options: ModelOptions) -> OllamaCompletionsRequest:
        ollama_options = {}
        
        if options.temperature is not None:
            ollama_options["temperature"] = options.temperature
        if options.top_p is not None:
            ollama_options["top_p"] = options.top_p
        if options.top_k_per_token is not None:
            ollama_options["top_k"] = options.top_k_per_token
        if options.max_tokens is not None:
            ollama_options["num_predict"] = options.max_tokens
        if options.stop_sequences:
            ollama_options["stop"] = options.stop_sequences
        if options.frequency_penalty is not None:
            ollama_options["repeat_penalty"] = options.frequency_penalty

        return OllamaCompletionsRequest(
            model=self.model,
            prompt=text,
            stream=False,
            options=ollama_options if ollama_options else None,
        )

    def evaluate(self, request: OllamaCompletionsRequest) -> OllamaCompletionsResponse:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        as_json = request.model_dump(exclude_none=True)
        
        try:
            response = _retrying_request(self._api_endpoint, headers, as_json, "POST")
            response_json = response.json()
            return OllamaCompletionsResponse(**response_json)
        except Exception as e:
            logger.error(f"Error calling Ollama API at {self._api_endpoint}: {e}")
            raise APIException(f"Ollama API call failed: {e}") from e

    def translate_response(self, request: OllamaCompletionsRequest, response: OllamaCompletionsResponse) -> SUTResponse:
        return SUTResponse(text=response.response)


# Register some common models that support LlamaGuard
SUTS.register(
    OllamaCompletionsSUT,
    "ollama-llama-guard3",
    "llama-guard3:latest",
    InjectSecret(OllamaApiKey),
    InjectSecret(OllamaBaseUrl),
)

SUTS.register(
    OllamaCompletionsSUT,
    "ollama-llama-guard2",
    "llama-guard2:latest",
    InjectSecret(OllamaApiKey),
    InjectSecret(OllamaBaseUrl),
)
