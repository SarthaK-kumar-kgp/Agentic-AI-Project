I want to defend againts 4 types of attack:
1. Prompt Injection (where the user asks the LLM to do what it is not supposed to do, or context bypassing, giving new persona)
2. Prompt leakage (The user forces the LLM into revealing its system prompt)
3. Malicious content output (where the attack is present inside the retreived document)
4. Detecting harmful work like bomb and stuffs or nudity or porn 


Idea:
Layer 0: We always normalize the text (ignore extra spaced ignore unicode ignore base64)

Layer 1: regex filters (can we detect pure malicious intent like bypass your instructions , or ignore the context, or act like, your are now, forget your instructions ) and this doesnt give a binary output, if its a perfect match its straighaway blocked, if its partial match like malicious word match it gets sent to next layer else pass

Layer 2: Semantic matching (we can have a list of toxic or harmful lines and we can do semantic matching if the match is really high we will block it for now, if its way too low we pass it and if its in between we need to maybe flag it or ask the user to rephrase it)

Layer 3: System prompt designing: it should have very good and clean design where the system prompt is specifically to always ignore overriding instructions in user prompt or the context retreived

Layer 4: Output check, given the output we can run a toxicity filter or profanity filter at the very end or same filters again to make sure user gets a clean output

Layer 5: Toxicity detecter if harmful word is detected always run it though the toxicity filter before sending it to the LLM this can run after the LLM output as well if needed