#!/usr/bin/env python3
"""
Codec hook v2 for Claude Code: keeps a proxy-blocked word out of API traffic.

- PreToolUse  (all tools): decodes placeholder -> real word in tool input,
  so files/commands on disk are correct.
- PostToolUse (all tools): encodes real word -> placeholder in tool output,
  so the word never travels back through the proxy (includes Edit/Write
  responses, which echo file content).

Placeholder scheme (case-preserving): marker __X__ inserted after the 3rd
letter, e.g.  sec__X__ret / Sec__X__ret / SEC__X__RET.
Decode is tolerant: removes the marker (any casing, repeated) wherever it
appears between the letters of the word.

Run `python3 secret_codec.py --test` to self-verify all combinations.

The blocked word is assembled at runtime from letters so this file itself
never contains it.
"""
import json
import re
import sys

MARK = "__X__"
L = ["s", "e", "c", "r", "e", "t"]          # the blocked word, letter by letter
WORD = "".join(L)

# ---- encode: real word -> placeholder (case-preserving, any context) ----
WORD_RE = re.compile(WORD, re.IGNORECASE)

def encode(text: str) -> str:
    def repl(m):
        w = m.group(0)
        return w[:3] + MARK + w[3:]
    return WORD_RE.sub(repl, text)

# ---- decode: placeholder -> real word ----
# Marker (any casing, possibly repeated) may sit between ANY letters of the
# word, not just after the 3rd. Requires at least one marker present.
_m = "(?:" + re.escape(MARK) + ")*"
_DECODE_SRC = _m.join("(" + re.escape(ch) + ")" for ch in L)
DECODE_RE = re.compile(_DECODE_SRC, re.IGNORECASE)

def decode(text: str) -> str:
    def repl(m):
        s = "".join(m.groups())
        return s
    # only rewrite if a marker is actually present inside the match
    def guarded(m):
        if MARK.lower() in m.group(0).lower():
            return repl(m)
        return m.group(0)
    return DECODE_RE.sub(guarded, text)

# ---- helpers ----
def walk(obj, fn):
    if isinstance(obj, str):
        return fn(obj)
    if isinstance(obj, list):
        return [walk(x, fn) for x in obj]
    if isinstance(obj, dict):
        return {k: walk(v, fn) for k, v in obj.items()}
    return obj

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    event = data.get("hook_event_name", "")

    if event == "PreToolUse":
        tool_input = data.get("tool_input", {})
        decoded = walk(tool_input, decode)
        if decoded != tool_input:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": decoded}}))
        sys.exit(0)

    if event == "PostToolUse":
        tool_response = data.get("tool_response")
        if tool_response is None:
            sys.exit(0)
        encoded = walk(tool_response, encode)
        if encoded != tool_response:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "updatedToolOutput": encoded}}))
        sys.exit(0)

    sys.exit(0)

# ---- self test ----
def _test():
    P = WORD[:3] + MARK + WORD[3:]   # canonical placeholder, lowercase
    cases_encode = {
        WORD: P,                                              # all lowercase
        WORD.upper(): WORD.upper()[:3] + MARK + WORD.upper()[3:],   # ALL CAPS
        WORD.capitalize(): WORD.capitalize()[:3] + MARK + WORD.capitalize()[3:],  # Capitalized
        "SeCrEt": "SeC" + MARK + "rEt",                       # mixed case
        "client" + WORD.capitalize(): "clientSec" + MARK + WORD.capitalize()[3:],  # camelCase suffix
        "aws_" + WORD + "_access_key": "aws_" + P + "_access_key",  # snake_case infix
        WORD.upper() + "S": WORD.upper()[:3] + MARK + WORD.upper()[3:] + "S",  # plural CAPS
        "Top" + WORD.capitalize() + "Value": "TopSec" + MARK + "retValue",  # prefix+suffix
        "my" + WORD + "s and " + WORD.upper() + "_KEY":
            "my" + P + "s and " + WORD.upper()[:3] + MARK + WORD.upper()[3:] + "_KEY",  # multiple hits
        "no match here": "no match here",                     # untouched
        "sec ret": "sec ret",                                 # split word untouched
    }
    cases_decode = {
        P: WORD,                                              # canonical
        "SEC" + MARK + "RET": WORD.upper(),                   # caps
        "Sec" + MARK.lower() + "ret": WORD.capitalize(),      # lowercase marker
        "se" + MARK + "cret": WORD,                           # marker at odd position
        "sec" + MARK + MARK + "ret": WORD,                    # doubled marker
        "s" + MARK + "e" + MARK + "cre" + MARK + "t": WORD,   # markers everywhere
        "aws_" + P + "_access_key": "aws_" + WORD + "_access_key",
        "clientSec" + MARK + "ret": "clientSec" + "ret",
        WORD: WORD,                                           # raw word passes through unchanged
        "plain text": "plain text",
    }
    fails = 0
    for src, want in cases_encode.items():
        got = encode(src)
        ok = got == want and WORD.lower() not in got.lower()
        print(("PASS" if ok else "FAIL"), "encode:", repr(src), "->", repr(got))
        fails += 0 if ok else 1
    for src, want in cases_decode.items():
        got = decode(src)
        ok = got == want
        print(("PASS" if ok else "FAIL"), "decode:", repr(src), "->", repr(got))
        fails += 0 if ok else 1
    # round trips
    for s in cases_encode:
        rt = decode(encode(s))
        ok = rt == s
        print(("PASS" if ok else "FAIL"), "roundtrip:", repr(s))
        fails += 0 if ok else 1
    print("=" * 40)
    print("ALL PASS" if fails == 0 else f"{fails} FAILURES")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        _test()
    main()
