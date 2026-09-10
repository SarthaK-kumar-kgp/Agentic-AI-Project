import json 
from regex_filters import RegexFilter
from semantic_checker import toxicity_check, semantic_similarity_check, harmful_intent_sentences
import torch

rf = RegexFilter()
def input_orchestrator(text):
    uni_text = rf.unicode_normalization(text)

    normalized_text = rf.normalize_text(uni_text)
    if normalized_text == "":
        return ""

    if rf.detect_prompt_injection(normalized_text) == "BLOCK":
        return {"decision":"BLOCK",
                "reason":"Prompt Injection Detected",
                "layer":"Layer 1"}
    if rf.detect_dangerous_content(normalized_text) == "BLOCK":
        return {"decision":"BLOCK | Dangerous Content Detected",
                "reason":"Dangerous Content Detected",
                "layer":"Layer 2"}
    if rf.detect_prompt_leakage(normalized_text) == "BLOCK":
        return {"decision":"BLOCK",
                "reason":"Prompt Leakage Detected",
                "layer":"Layer 3"}

    if rf.detect_alarming_words(normalized_text)=="WARNING":
        if toxicity_check(text)['toxicity']>0.5:
            return {"decision":"BLOCK",
                    "reason":"Toxicity Detected",
                    "layer":"Layer 4"}
        elif semantic_similarity_check(text, harmful_intent_sentences).max() >= 0.5:
            return {"decision":"BLOCK",
                    "reason":"Dangerous Intent Detected",
                    "layer":"Layer 4"}
        
        else:
            return {"decision":"ALLOW ",
                    "reason":"No dangerous intent detected",
                    "layer":"Layer 4"}
    else:
        return {"decision":"ALLOW",
                "reason":"Didnt pass through any filters",
                "layer":"Layer 4"}


    

