"""Offline o200k_base encode_ordinary with frozen ranks and regex pretokenization.

Reference byte-pair merging, compatible with tiktoken 0.12.0. No model calls,
network, normalisation, implicit user cache or unsupported binary ABI loading.
The optional test harness compares token IDs with the archived native encoder.
"""
from __future__ import annotations
import base64, hashlib, json, sys
from pathlib import Path
from functools import lru_cache

try:
    import regex
except ImportError:
    vendor = Path(__file__).resolve().parents[1] / 'vendor' / 'runtime_cp313_linux'
    if sys.version_info[:2] == (3,13) and sys.platform == 'linux' and vendor.exists():
        sys.path.insert(0, str(vendor))
        import regex
    else:
        raise RuntimeError('Install regex==2026.5.9 from requirements.txt; no tokenizer approximation is allowed.') from None

class Encoder:
    def __init__(self, directory: Path | None = None):
        d = directory or Path(__file__).resolve().parents[1] / 'vendor' / 'tokenizer'
        self.config = json.loads((d / 'tokenizer_config.json').read_text(encoding='utf-8'))
        raw = (d / 'o200k_base.tiktoken').read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != self.config['mergeable_ranks_sha256']:
            raise ValueError('Frozen tokenizer vocabulary hash mismatch')
        self.ranks = {base64.b64decode(b): int(i) for b,i in (l.split() for l in raw.splitlines())}
        self.pattern = regex.compile(self.config['pat_str'])
        self.audit = {'implementation':'reference_BPE_encode_ordinary','compatible_contract':'tiktoken==0.12.0/o200k_base', 'native_tiktoken_used':False, 'regex_version':regex.__version__, 'ranks_sha256':self.sha256, 'whole_text_cache':False,'piece_cache_maxsize':200000}

    @lru_cache(maxsize=200000)
    def piece(self, text: str) -> tuple[int, ...]:
        data = text.encode('utf-8',errors='strict')
        if data in self.ranks:
            return (self.ranks[data],)
        parts = [bytes([b]) for b in data]
        while len(parts) > 1:
            best_rank = None
            best_i = None
            for i in range(len(parts)-1):
                rank = self.ranks.get(parts[i]+parts[i+1])
                if rank is not None and (best_rank is None or rank < best_rank):
                    best_rank, best_i = rank, i
            if best_i is None:
                break
            parts[best_i:best_i+2] = [parts[best_i]+parts[best_i+1]]
        return tuple(self.ranks[p] for p in parts)

    def encode(self, text: str) -> tuple[int, ...]:
        if not isinstance(text, str):
            raise TypeError('Tokenizer input must be a string')
        text.encode('utf-8',errors='strict')
        return tuple(t for p in self.pattern.findall(text) for t in self.piece(p))

    def count(self, text: str) -> int:
        return len(self.encode(text))
