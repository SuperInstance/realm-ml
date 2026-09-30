import re
# Which quantity is the claim making dominant? Look at the noun phrase before the verb.
#   "relationship weight dominates the stimulus"  -> dominant = weight
#   "the stimulus dominates relationship weight"  -> dominant = stimulus
WEIGHT_WORDS = re.compile(r'\b(weight|weights|weighting|edge|edges|relationship|relationships)\b', re.I)
STIM_WORDS  = re.compile(r'\b(stimulus|stimuli|stim|input|inputs)\b', re.I)
DOM_VERB    = re.compile(
    r'(\S+(?:\s+\S+)?)\s+(?:dominates?|overrides?|wins? over|beats?)\s+'
    r'(?:the\s+|a\s+|an\s+|its\s+|their\s+)?(\S+(?:\s+\S+)?)', re.I)
def direction(claim):
    m = DOM_VERB.search(claim)
    if not m: return None
    subj, obj = m.group(1), m.group(2)
    def kind(phrase):
        head = phrase.split()[-1] if phrase.split() else ""
        s = WEIGHT_WORDS.search(phrase); t = STIM_WORDS.search(phrase)
        if s and not t: return "weight"
        if t and not s: return "stim"
        # fall back to the nearest word inside the phrase
        if STIM_WORDS.search(head): return "stim"
        if WEIGHT_WORDS.search(head): return "weight"
        return None
    return kind(subj), kind(obj)
