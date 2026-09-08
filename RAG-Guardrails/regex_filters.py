import pandas as pd 
import numpy as np
import re 
import unicodedata

class RegexFilter:
    def unicode_normalization(self,text=None):
        if text is None:
            return ""
        self.unicode_normalize = unicodedata.normalize('NFKD', text).casefold()
        return self.unicode_normalize


    def normalize_text(self,text):
        if text is None:
            return ""

        self.normalized_text = text.strip().replace(" ","")
        return self.normalized_text

    def detect_prompt_injection(self,text):
        if text is None:
            return False
        self.prompt_injection_pattern = r"(ignore.*instructions|disregard.*instructions|forget.*instructions| \
                                           override.*instructions|act.*as.*an.*expert|act.*as.*specialist|act.*as.*professional)" 
        if re.search(self.prompt_injection_pattern,text):
            return "BLOCK"
        else:
            return "ALLOW"

    def detect_dangerous_content(self,text):
        if text is None:
            return False
        self.dangerous_content_pattern = r"(how.*to.*hack|how.*to.*steal|how.*to.*kill|how.*to.*bomb|\
                                           bypass.*security|how.*to.*exploit|how.*to.*assasinate|how.*to.*fraud|how.*to.*scam)"
        if re.search(self.dangerous_content_pattern,text):
            return "BLOCK"
        else:
            return "ALLOW"
    def detect_prompt_leakage(self,text):
            
