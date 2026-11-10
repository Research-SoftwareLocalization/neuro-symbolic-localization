"""
Core Deterministic Invariant Verifier for Software Localization Catalogs
Implements linear-time verification for six formal localization invariants:
  - I_script: Orthographic script purity & digraphic boundary enforcement
  - I_ph: Positional placeholder multiset parity & failure decomposition
  - I_acc: Keyboard mnemonic accelerator preservation
  - I_enc: Subword byte-level UTF-8 decoding integrity (U+FFFD suppression)
  - I_chat: Zero conversational framing & preamble suppression
  - I_ntt: Semantic non-echoing with domain-aware non-translatable tokens
"""

import re
from typing import Dict, Tuple, Set

# Regex patterns defined in the formal specification
REGEX_PH = re.compile(r'%\d+|%\w+|\{[^\}]+\}')
REGEX_XML = re.compile(r'&[a-zA-Z0-9.\-]+;')
REGEX_ACC = re.compile(r'&[^\s\d_;]')
REGEX_CHAT = re.compile(
    r'(?i)^(here is the translation|translation:|note:|as an ai|translate into|arabic:|spanish:|bengali:)',
    re.IGNORECASE
)

# Forbidden Unicode block ranges for script purity (I_script)
FORBIDDEN_SCRIPTS = {
    'indic': {'cjk': (0x4E00, 0x9FFF), 'hangul': (0xAC00, 0xD7AF), 'cyrillic': (0x0400, 0x04FF), 'arabic': (0x0600, 0x06FF)},
    'latin_eu': {'cjk': (0x4E00, 0x9FFF), 'hangul': (0xAC00, 0xD7AF), 'cyrillic': (0x0400, 0x04FF), 'arabic': (0x0600, 0x06FF)},
    'punjabi_in': {'shahmukhi': (0x0600, 0x06FF), 'cjk': (0x4E00, 0x9FFF), 'hangul': (0xAC00, 0xD7AF)}
}

def verify_script_purity(h: str, locale: str) -> bool:
    """I_script: Audits target string for out-of-alphabet foreign codepoints."""
    codepoints = [ord(c) for c in h]
    
    # Specific rule for Punjabi in India (pa-IN): strictly forbid Perso-Arabic Shahmukhi
    if locale == 'pa':
        for cp in codepoints:
            if 0x0600 <= cp <= 0x06FF:
                return False
                
    # General foreign script block checks
    ranges = FORBIDDEN_SCRIPTS.get('indic' if locale in {'bn', 'hi', 'mr', 'pa', 'ta', 'te'} else 'latin_eu', {})
    for start, end in ranges.values():
        for cp in codepoints:
            if start <= cp <= end:
                return False
    return True

def verify_placeholder_parity(s: str, h: str) -> Tuple[bool, str]:
    """I_ph: Verifies multiset parity of format specifiers and decomposes errors."""
    p_s = REGEX_PH.findall(s)
    p_h = REGEX_PH.findall(h)
    
    if p_s == p_h:
        return True, "PASS"
    
    # Error classification per formal decomposition
    if len(p_s) > 0 and len(p_h) == 0:
        return False, "E_omit"
    elif len(p_s) == 0 and len(p_h) > 0:
        return False, "E_halluc"
    else:
        return False, "E_mut"

def verify_keyboard_accelerator(s: str, h: str) -> bool:
    """I_acc: Verifies preservation of hotkey ampersands."""
    def clean_xml(text: str) -> str:
        return REGEX_XML.sub('', text)
    
    s_clean = clean_xml(s)
    h_clean = clean_xml(h)
    
    has_acc_s = bool(REGEX_ACC.search(s_clean))
    has_acc_h = bool(REGEX_ACC.search(h_clean))
    
    if has_acc_s and not has_acc_h:
        return False
    return True

def verify_utf8_integrity(h: str) -> bool:
    """I_enc: Checks for unescaped subword byte-split replacement characters (U+FFFD)."""
    return '\ufffd' not in h

def verify_chatter_suppression(h: str) -> bool:
    """I_chat: Suppresses conversational AI preambles and meta-text."""
    return not bool(REGEX_CHAT.search(h.strip()))

def verify_non_echoing(s: str, h: str, locale: str) -> bool:
    """I_ntt: Audits invalid copy-fallback while respecting non-translatable tokens."""
    s_trim = s.strip()
    h_trim = h.strip()
    
    # If source is long enough and identical to hypothesis, flag unless whitelisted
    if s_trim == h_trim and len(s_trim) > 3:
        # Basic whitelist check for standard technical cognates/paths
        if any(token in s_trim for token in ['/', 'http', 'API', 'URL', 'Samba', 'CD-ROM']):
            return True
        return False
    return True

def audit_segment(s: str, h: str, locale: str) -> Dict[str, any]:
    """Executes all 6 deterministic invariant checks on a single source-hypothesis pair."""
    i_script = verify_script_purity(h, locale)
    i_ph, ph_error_type = verify_placeholder_parity(s, h)
    i_acc = verify_keyboard_accelerator(s, h)
    i_enc = verify_utf8_integrity(h)
    i_chat = verify_chatter_suppression(h)
    i_ntt = verify_non_echoing(s, h, locale)
    
    is_compliant = all([i_script, i_ph, i_acc, i_enc, i_chat, i_ntt])
    
    return {
        "compliant": is_compliant,
        "invariants": {
            "I_script": i_script,
            "I_ph": i_ph,
            "I_acc": i_acc,
            "I_enc": i_enc,
            "I_chat": i_chat,
            "I_ntt": i_ntt
        },
        "ph_error_type": ph_error_type if not i_ph else None
    }
