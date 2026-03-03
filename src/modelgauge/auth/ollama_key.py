from modelgauge.secret_values import OptionalSecret, SecretDescription


class OllamaApiKey(OptionalSecret):
    """
    API key for Ollama. Since Ollama typically runs locally without authentication,
    this is optional. However, it can be used for remote Ollama instances that require auth.
    """

    @classmethod
    def description(cls) -> SecretDescription:
        return SecretDescription(
            scope="ollama",
            key="api_key",
            instructions="Optional: API key for remote Ollama instances. Leave empty for local Ollama.",
        )


class OllamaBaseUrl(OptionalSecret):
    """
    Base URL for Ollama API. Defaults to http://localhost:11434 if not provided.
    """

    @classmethod
    def description(cls) -> SecretDescription:
        return SecretDescription(
            scope="ollama",
            key="base_url",
            instructions="Base URL for Ollama API (default: http://localhost:11434)",
        )
