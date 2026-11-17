"""Safe, language-independent numeric artifact serialization; no pickle."""
from __future__ import annotations
import operator

def normalize_vocabulary(source:dict)->dict[str,int]:
    if not isinstance(source,dict) or not source:raise ValueError("VOCAB_EMPTY")
    normalized={}
    seen=set()
    for token,index in source.items():
        if not isinstance(token,str) or not token or isinstance(index,bool):
            raise ValueError("BAD_VOCAB_ENTRY")
        value=operator.index(index)  # accepts numpy.integer but rejects floats.
        if value<0 or value in seen:raise ValueError("BAD_VOCAB_INDEX")
        seen.add(value)
        normalized[token]=int(value)
    if seen!=set(range(len(normalized))):raise ValueError("NONCONTIGUOUS_VOCAB")
    return normalized
