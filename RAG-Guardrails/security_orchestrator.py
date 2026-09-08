import numpy as np
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
        return "BLOCK | Prompt Injection Detected"
    if rf.detect_dangerous_content(normalized_text) == "BLOCK":
        return "BLOCK | Dangerous Content Detected"
    if rf.detect_prompt_leakage(normalized_text) == "BLOCK":
        return "BLOCK | Prompt Leakage Detected"

    if rf.detect_alarming_words(normalized_text)=="WARNING":
        if toxicity_check(text)['toxicity']>0.5:
            return "BLOCK | Toxicity Detected"
        elif semantic_similarity_check(text, harmful_intent_sentences).max() > 0.7:
            return "BLOCK | Dangerous Intent Detected"
        else:
            return "ALLOW | No Alarming Words Detected"


    







# Layer 0
# Layer 1 where we do exact checks 
# Layer 2 where we do keyword matching  
# Layer 3 where we do toxicity matching one which passes is flagged fails 
# Layser 4 one which passes goes to semantic match 
# Layer All prompt cleaning