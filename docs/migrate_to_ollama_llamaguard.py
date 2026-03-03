#!/usr/bin/env python3
"""
Quick Migration Script: Switch from Together API to Ollama LlamaGuard

This script shows exactly what needs to change to switch from Together API's
llama_guard_2 to local Ollama's ollama_llama_guard_3.

To apply these changes manually, follow the instructions below.
"""

# =============================================================================
# FILE 1: src/modelgauge/tests/safe_v1.py
# =============================================================================
# LOCATION: Around line 219
# CHANGE: Update get_annotators() method
"""
BEFORE:
-------
@modelgauge_test(requires_sut_capabilities=[AcceptsTextPrompt])
class SafeTestVersion1(BaseSafeTestVersion1):
    @classmethod
    def get_annotators(cls) -> List[str]:
        return ["llama_guard_2"]

AFTER:
------
@modelgauge_test(requires_sut_capabilities=[AcceptsTextPrompt])
class SafeTestVersion1(BaseSafeTestVersion1):
    @classmethod
    def get_annotators(cls) -> List[str]:
        return ["ollama_llama_guard_3"]
"""

# =============================================================================
# FILE 2: src/modelgauge/tests/security.py
# =============================================================================
# LOCATION: Around line 134
# CHANGE: Update SecurityNaiveTest.get_annotators()
"""
BEFORE:
-------
@modelgauge_test(requires_sut_capabilities=[AcceptsTextPrompt])
class SecurityNaiveTest(BaseSecurityNaiveTest):
    @classmethod
    def get_annotators(cls) -> List[str]:
        return ["llama_guard_2"]

AFTER:
------
@modelgauge_test(requires_sut_capabilities=[AcceptsTextPrompt])
class SecurityNaiveTest(BaseSecurityNaiveTest):
    @classmethod
    def get_annotators(cls) -> List[str]:
        return ["ollama_llama_guard_3"]
"""

# LOCATION: Around line 154
# CHANGE: Update SecurityJailbreakTest.get_annotators()
"""
BEFORE:
-------
@modelgauge_test(requires_sut_capabilities=[AcceptsTextPrompt])
class SecurityJailbreakTest(BaseSecurityJailbreakTest):
    @classmethod
    def get_annotators(cls) -> List[str]:
        return ["llama_guard_2"]

AFTER:
------
@modelgauge_test(requires_sut_capabilities=[AcceptsTextPrompt])
class SecurityJailbreakTest(BaseSecurityJailbreakTest):
    @classmethod
    def get_annotators(cls) -> List[str]:
        return ["ollama_llama_guard_3"]
"""

# =============================================================================
# PREREQUISITES
# =============================================================================
print("""
PREREQUISITES CHECKLIST:
========================

Before making the changes above, ensure:

1. ✓ Ollama is installed
   $ curl -fsSL https://ollama.ai/install.sh | sh

2. ✓ LlamaGuard model is pulled
   $ ollama pull llama-guard3

3. ✓ Ollama is running
   $ curl http://localhost:11434/api/version
   
   If not running, start it:
   $ ollama serve

4. ✓ Test the annotator works
   $ python src/modelgauge/annotators/ollama_llama_guard_annotator.py "test message"

""")

# =============================================================================
# SUMMARY OF CHANGES
# =============================================================================
print("""
SUMMARY OF CHANGES:
===================

Total files to modify: 2
Total lines to change: 3

1. src/modelgauge/tests/safe_v1.py (line ~219)
   Change: "llama_guard_2" → "ollama_llama_guard_3"

2. src/modelgauge/tests/security.py (lines ~134 and ~154)
   Change: "llama_guard_2" → "ollama_llama_guard_3" (2 occurrences)

""")

# =============================================================================
# BENEFITS
# =============================================================================
print("""
BENEFITS OF THIS CHANGE:
=========================

✓ No API costs (runs locally)
✓ No API rate limits
✓ Better privacy (data stays local)
✓ Works offline
✓ Faster for batch processing

""")

# =============================================================================
# TESTING
# =============================================================================
print("""
TESTING THE CHANGES:
====================

After making the changes, test with:

1. Run a simple test:
   $ modelbench test --sut demo_yes_no --test safe-dfm-1.0

2. Run a full benchmark:
   $ modelbench benchmark --sut your-model --benchmark general_purpose_ai_chat_benchmark-1.0

3. Check logs to verify Ollama is being used:
   $ tail -f ~/.modelbench/logs/benchmark.log
   
   Look for: localhost:11434 (Ollama) instead of api.together.xyz (Together API)

""")

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*80)
    print("MIGRATION GUIDE: Together API → Ollama LlamaGuard")
    print("="*80 + "\n")
    
    response = input("Would you like to see the exact file locations? (y/n): ").strip().lower()
    
    if response in ['y', 'yes']:
        import os
        workspace = "/home/arunsuresh/modelbench"
        
        files_to_edit = [
            f"{workspace}/src/modelgauge/tests/safe_v1.py",
            f"{workspace}/src/modelgauge/tests/security.py",
        ]
        
        print("\nFILES TO EDIT:\n")
        for i, file_path in enumerate(files_to_edit, 1):
            exists = "✓ EXISTS" if os.path.exists(file_path) else "✗ NOT FOUND"
            print(f"{i}. {file_path} [{exists}]")
        
        print("\nTo edit these files, use your favorite editor:")
        print(f"  vim {files_to_edit[0]}")
        print(f"  vim {files_to_edit[1]}")
        
    print("\n" + "="*80)
    print("For more details, see:")
    print("  src/modelgauge/annotators/OLLAMA_LLAMAGUARD_README.md")
    print("="*80 + "\n")
