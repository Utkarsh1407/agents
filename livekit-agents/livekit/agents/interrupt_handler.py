import re

FILLER_BASE = {
    "hmm", "hm", "um", "uh", "mmm", "mm", "umm", 
    "erm", "eh", "huh", "mhmm", "uh-huh", "mm-hmm"
}

MIN_CONFIDENCE = 0.60
_TOKEN_RE = re.compile(r"[A-Za-z0-9'-]+")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split()).lower().strip()


def tokenize(text: str):
    return _TOKEN_RE.findall(text or "")


def is_pure_hmu(token: str) -> bool:
    """Token is made only of h,m,u → typical filler patterns."""
    return token and all(ch in {"h", "m", "u"} for ch in token)


def token_is_filler(token: str) -> bool:
    t = token.lower()

    if t in FILLER_BASE:
        return True
    if is_pure_hmu(t):
        return True
    if len(t) <= 2:
        return True

    return False


def is_filler_sequence(tokens: list) -> bool:
    if not tokens:
        return True
    return all(token_is_filler(tk) for tk in tokens)



async def handle_transcript_event(session, text: str, confidence: float, agent_instance=None):
    raw = text or ""
    t = normalize_text(raw)
    conf = confidence or 0.0

    print(f"[RECEIVED] text='{raw}'  normalized='{t}'  conf={conf}")

    # Check the agent's speaking state using the manual flag
    was_speaking = agent_instance.is_agent_speaking if agent_instance else False
    
    # --- IGNORED CASES (Filler/Noise) ---
    is_filler_or_low_conf = (
        not t or 
        conf < MIN_CONFIDENCE or 
        is_filler_sequence(tokenize(t))
    )
    
    if is_filler_or_low_conf:
        reason = "empty/filler/low confidence"
        print(f"[IGNORED] reason={reason}")
        
        # Only send 'resume' action if the agent was actually speaking
        if was_speaking:
            print("[RESUMING] Forcing agent to resume previous speech.")
            return {"action": "resume"}
        
        return None # Do nothing if agent wasn't speaking

    # 4) REAL INTERRUPTION → Stop the agent

    print(f"[INTERRUPT] reason=real speech  text='{t}'")
    return {
        "action": "stop",
        "text": t
    }