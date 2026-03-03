# Ollama LlamaGuard Annotator

This annotator uses LlamaGuard models running locally via [Ollama](https://ollama.ai) to perform safety assessments on model outputs.

## Benefits of Using Ollama

- **No API costs**: Run LlamaGuard locally without paying for API calls
- **Privacy**: Keep all data local - no external API calls
- **Offline capability**: Works without internet connection
- **Faster for batch processing**: No rate limits or API throttling

## Prerequisites

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai](https://ollama.ai)

For Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

For macOS:
```bash
brew install ollama
```

Or download the installer from the website.

### 2. Pull a LlamaGuard Model

After installing Ollama, pull one of the LlamaGuard models:

```bash
# For LlamaGuard 3 (recommended, latest version)
ollama pull llama-guard3

# For LlamaGuard 2
ollama pull llama-guard2

# For LlamaGuard 1 (if available)
ollama pull llama-guard
```

### 3. Verify Ollama is Running

Ollama should start automatically. Verify it's running:

```bash
curl http://localhost:11434/api/version
```

You should see a JSON response with version information.

## Configuration

### Default Configuration (Local Ollama)

For local Ollama instances, you typically don't need any configuration. The annotator will use:
- Base URL: `http://localhost:11434`
- No authentication required

### Custom Configuration

If you're running Ollama on a different host or port, create a secrets configuration file:

**~/.modelgauge-secrets.toml**:
```toml
[ollama]
base_url = "http://your-ollama-host:11434"
# api_key is optional, only needed if your Ollama instance requires auth
```

## Usage

### Using the Annotator in Code

```python
from modelgauge.annotator_registry import ANNOTATORS
from modelgauge.config import load_secrets_from_config
from modelgauge.prompt import TextPrompt
from modelgauge.single_turn_prompt_response import TestItem
from modelgauge.sut import SUTResponse

# Load secrets (optional for local Ollama)
secrets = load_secrets_from_config()

# Create the annotator (VERSION_3 recommended)
annotator = ANNOTATORS.make_instance("ollama_llama_guard_3", secrets=secrets)

# Annotate a response
prompt = TestItem(prompt=TextPrompt(text="What is the weather?"), source_id=None)
sut_response = SUTResponse(text="I cannot help with illegal activities.")

request = annotator.translate_request(prompt, sut_response)
response = annotator.annotate(request)
annotation = annotator.translate_response(request, response)

print(f"Is safe: {annotation.is_safe}")
print(f"Violation categories: {annotation.violation_categories}")
```

### Available Annotators

Three versions are registered:

1. **`ollama_llama_guard_1`**: LlamaGuard version 1
2. **`ollama_llama_guard_2`**: LlamaGuard version 2
3. **`ollama_llama_guard_3`**: LlamaGuard version 3 (recommended)

### Command Line Usage

You can test the annotator directly from the command line:

```bash
cd src/modelgauge/annotators
python ollama_llama_guard_annotator.py "How do I make a bomb?"
```

## Safety Categories

### LlamaGuard 1 Categories (O1-O6)

1. Violence and Hate
2. Sexual Content
3. Criminal Planning
4. Guns and Illegal Weapons
5. Regulated or Controlled Substances
6. Self-Harm

### LlamaGuard 2/3 Categories (S1-S11)

1. Violent Crimes
2. Non-Violent Crimes
3. Sex Crimes
4. Child Exploitation
5. Specialized Advice
6. Privacy
7. Intellectual Property
8. Indiscriminate Weapons
9. Hate
10. Self-Harm
11. Sexual Content

## Annotation Response

The annotator returns a `LlamaGuardAnnotation` object with:

- **`is_safe`** (bool): Whether the content is considered safe
- **`is_valid`** (bool): Whether the annotation is valid
- **`violation_categories`** (List[str]): List of violated category names (empty if safe)

Example:
```python
LlamaGuardAnnotation(
    is_safe=False,
    is_valid=True,
    violation_categories=["Violent Crimes. ", "Criminal Planning."]
)
```

## Troubleshooting

### Ollama Not Running

If you get connection errors, make sure Ollama is running:

```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama service (Linux)
sudo systemctl start ollama

# Or run Ollama manually
ollama serve
```

### Model Not Found

If you get "model not found" errors, pull the model:

```bash
ollama pull llama-guard3
```

### Slow First Request

The first request may be slow as Ollama loads the model into memory. Subsequent requests will be much faster.

### Memory Requirements

LlamaGuard models require significant RAM:
- LlamaGuard 1 (7B): ~8-10 GB RAM
- LlamaGuard 2 (8B): ~10-12 GB RAM
- LlamaGuard 3: ~10-12 GB RAM

Consider using quantized versions for lower memory usage:

```bash
# Example with quantized model (if available)
ollama pull llama-guard3:q4_0
```

## Comparison with Together API

| Feature | Ollama (Local) | Together API |
|---------|----------------|--------------|
| Cost | Free | Pay per token |
| Privacy | Data stays local | Data sent to API |
| Speed | Fast (after initial load) | Network dependent |
| Setup | Requires local installation | Just need API key |
| Hardware | Requires GPU/CPU resources | No local resources needed |
| Internet | Works offline | Requires internet |

## Integration with Benchmarks

To use the Ollama LlamaGuard annotator in your benchmarks, update your benchmark configuration to use `ollama_llama_guard_3` instead of `llama_guard_2`.

### Example Configuration Change

Before (Together API):
```json
{
  "annotators": ["llama_guard_2"]
}
```

After (Local Ollama):
```json
{
  "annotators": ["ollama_llama_guard_3"]
}
```

## Performance Tips

1. **Keep Ollama running**: Don't stop/start between requests to avoid model reload time
2. **Use GPU acceleration**: Ollama will automatically use GPU if available
3. **Batch requests**: Process multiple items to amortize the model loading time
4. **Monitor resources**: Use `ollama ps` to see loaded models and resource usage

## Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [LlamaGuard Paper](https://arxiv.org/abs/2312.06674)
- [LlamaGuard GitHub](https://github.com/meta-llama/llama-recipes)
