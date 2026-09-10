import re 
import unicodedata
import base64
import codecs

class RegexFilter:

    
    def unicode_normalization(self,text=None):
        if text is None:
            return ""
        self.unicode_normalize = unicodedata.normalize('NFKD', text).casefold()
        return self.unicode_normalize


    def normalize_text(self,text):
        if text is None:
            return ""

        self.normalized_text = text.lower().strip().replace(" ","")
        return self.normalized_text

    def detect_prompt_injection(self,text):
        if text is None:
            return False
        self.prompt_injection_pattern = r"(ignore.*instruction(s)?|disregard.*instruction(s)?|forget.*instructions|ignore.*context|ignore.*guardrail(s)?|\
                                           override.*instruction(s)?|act.*as.*an.*expert|act.*as.*specialist|act.*as.*professional)" 
        if re.search(self.prompt_injection_pattern,text,re.IGNORECASE | re.VERBOSE):
            return "BLOCK"
        else:
            return "ALLOW"

    def detect_dangerous_content(self,text):
        if text is None:
            return False
        self.dangerous_content_pattern = r"(how.*to.*hack|how.*to.*steal|how.*to.*kill|how.*to.*bomb|\
                                           bypass.*security|how.*to.*exploit|how.*to.*assasinate|how.*to.*fraud|how.*to.*scam)"
        if re.search(self.dangerous_content_pattern,text,re.IGNORECASE | re.VERBOSE):
            return "BLOCK"
        else:
            return "ALLOW"
    def detect_prompt_leakage(self,text):
        if text is None:
            return False
        
        self.prompt_leakage_pattern = r"(leak.*prompt|expose.*prompt|reveal.*prompt|display.*prompt|reveal.*instructions|expose.*instructions|display.*instructions|leak.*instructions)"
        if re.search(self.prompt_leakage_pattern,text,re.IGNORECASE | re.VERBOSE):
            return "BLOCK"
        else:
            return "ALLOW"

    def detect_alarming_words(self,text):
        if text is None:
            return False
        self.dangerous_words = r"(kill|bomb|assasinate|fraud|scam|porn|nudity|drugs|guns|violence|violent|bypass|override|disregard|\
                                  |suicide|terrorism|terrorist|explosive(s)?|malware|cyberattack|hack(ing)?|ignore|instructions|\
                                    phishing|spyware|bribery|blackmail|cheating|corruption|fake|forgery|illegal)"
        if re.search(self.dangerous_words,text,re.IGNORECASE | re.VERBOSE):
            return "WARNING"
        else:
            return "ALLOW"

            
