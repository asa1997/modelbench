# Quick Answer: Where to Use `ollama_llama_guard_3`

## TL;DR - Three Places to Use It

### 1. 🎯 **In Test Classes** (MOST COMMON - This is probably what you want!)

When you define safety tests, specify which annotator to use in the `get_annotators()` method:

**Location:** `src/modelgauge/tests/safe_v1.py` (line ~219)

```python
@modelgauge_test(requires_sut_capabilities=[AcceptsTextPrompt])
class SafeTestVersion1(BaseSafeTestVersion1):
    @classmethod
    def get_annotators(cls) -> List[str]:
        return ["ollama_llama_guard_3"]  # <-- Change this line!
```

**Location:** `src/modelgauge/tests/security.py` (lines ~134, ~154)

```python
@modelgauge_test(requires_sut_capabilities=[AcceptsTextPrompt])
class SecurityNaiveTest(BaseSecurityNaiveTest):
    @classmethod
    def get_annotators(cls) -> List[str]:
        return ["ollama_llama_guard_3"]  # <-- Change this line!
```

### 2. 🔧 **In Standalone Scripts** (For testing/debugging)

```python
from modelgauge.annotator_registry import ANNOTATORS

# This is what you showed - it creates an annotator instance
annotator = ANNOTATORS.make_instance("ollama_llama_guard_3", secrets={})

# Then use it to annotate responses
from modelgauge.sut import SUTResponse
from modelgauge.prompt import TextPrompt
from modelgauge.single_turn_prompt_response import TestItem

prompt = TestItem(prompt=TextPrompt(text="prompt"), source_id="test")
response = SUTResponse(text="The response to evaluate")

request = annotator.translate_request(prompt, response)
annotation_response = annotator.annotate(request)
annotation = annotator.translate_response(request, annotation_response)

print(f"Safe: {annotation.is_safe}")
print(f"Violations: {annotation.violation_categories}")
```

### 3. 🚀 **Via Command Line** (Automatic when you run benchmarks)

Once you update the test classes (option 1 above), the annotator is automatically used:

```bash
modelbench benchmark --sut your-model --benchmark general_purpose_ai_chat_benchmark-1.0
```

The system automatically:
- Reads which tests to run
- Checks what annotators each test needs (via `get_annotators()`)
- Creates instances: `ANNOTATORS.make_instance("ollama_llama_guard_3", secrets={})`
- Applies them to all responses

---

## What You Should Do

**For Production Use (recommended):**
1. Edit the test files to change `"llama_guard_2"` → `"ollama_llama_guard_3"`
2. Run your benchmarks normally - it will automatically use Ollama

**For Quick Testing:**
1. Use the code snippet you showed directly in a Python script
2. Good for one-off evaluations or debugging

---

## Complete Example

See this working example:
```bash
python examples/ollama_llamaguard_example.py
```

Or run interactively:
```bash
python examples/ollama_llamaguard_example.py --interactive
```

---

## Files to Modify for Full Integration

| File | Line | What to Change |
|------|------|----------------|
| `src/modelgauge/tests/safe_v1.py` | ~219 | `"llama_guard_2"` → `"ollama_llama_guard_3"` |
| `src/modelgauge/tests/security.py` | ~134 | `"llama_guard_2"` → `"ollama_llama_guard_3"` |
| `src/modelgauge/tests/security.py` | ~154 | `"llama_guard_2"` → `"ollama_llama_guard_3"` |

---

## Need Help?

Run this migration guide:
```bash
python docs/migrate_to_ollama_llamaguard.py
```

Read the full documentation:
```bash
cat src/modelgauge/annotators/OLLAMA_LLAMAGUARD_README.md
```
