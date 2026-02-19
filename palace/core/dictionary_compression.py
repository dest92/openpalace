"""
Dictionary Compression for Code Patterns - V2 Optimization

Compress common code patterns using dictionary encoding.

Based on:
- LZ77 dictionary compression
- Dictionary encoding in ClickHouse
- Pattern compression in source code

Goal: 30-40% additional compression on repetitive patterns.
"""

import hashlib
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import Counter


@dataclass
class DictionaryEntry:
    """Entry in compression dictionary."""
    pattern: str
    code: int  # Single byte encoding (0-255)
    frequency: int


class CodePatternDictionary:
    """
    Dictionary for common code patterns.

    Automatically learns patterns from code and compresses them.

    Common patterns in source code:
    - "def " (function definition)
    - "class " (class definition)
    - "import " (import statement)
    - "return " (return statement)
    - "if __name__" (main guard)
    - "self." (instance access)
    - "None" (null value)
    """

    # Default common patterns
    DEFAULT_PATTERNS = [
        "def ",
        "class ",
        "import ",
        "from ",
        "return ",
        "self.",
        "None",
        "True",
        "False",
        "if ",
        "else:",
        "elif ",
        "for ",
        "while ",
        "with ",
        "try:",
        "except ",
        "raise ",
        "assert ",
        "pass",
        "break",
        "continue",
        "async def",
        "await ",
    ]

    def __init__(self, max_entries: int = 256):
        """
        Initialize dictionary.

        Args:
            max_entries: Maximum dictionary entries (default: 256 = 1 byte)
        """
        self.max_entries = max_entries
        self.patterns: Dict[str, int] = {}
        self.reverse_patterns: Dict[int, str] = {}
        self.frequencies: Counter = Counter()

        # Initialize with default patterns
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Initialize with common code patterns."""
        for i, pattern in enumerate(self.DEFAULT_PATTERNS):
            if i < self.max_entries:
                code = i + 1  # Reserve 0 for "no encoding"
                self.patterns[pattern] = code
                self.reverse_patterns[code] = pattern
                self.frequencies[pattern] = 1000  # High frequency for defaults

    def learn_from_code(self, code: str) -> None:
        """
        Learn patterns from code.

        Args:
            code: Source code to analyze
        """
        # Find n-grams (sequences of characters)
        for length in [3, 4, 5]:
            for i in range(len(code) - length):
                ngram = code[i:i+length]

                # Must be alphanumeric + common chars
                if self._is_valid_pattern(ngram):
                    self.frequencies[ngram] += 1

        # Update dictionary if we have space
        self._update_dictionary()

    def _is_valid_pattern(self, pattern: str) -> bool:
        """
        Check if pattern is valid for dictionary.

        Valid patterns:
        - Alphanumeric + underscore
        - Common keywords (def, class, if, etc.)
        - Operators (=, ==, !=, etc.)

        Args:
            pattern: Pattern to validate

        Returns:
            True if pattern should be in dictionary
        """
        # Must be at least 3 chars
        if len(pattern) < 3:
            return False

        # Must start with letter or underscore
        if not (pattern[0].isalpha() or pattern[0] in '_.'):
            return False

        # All chars must be valid
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.,:()[]{}+-=<>&|!')
        return all(c in valid_chars for c in pattern)

    def _update_dictionary(self) -> None:
        """Update dictionary with high-frequency patterns."""
        # Get top patterns
        top_patterns = self.frequencies.most_common(self.max_entries * 2)

        for pattern, freq in top_patterns:
            if len(self.patterns) >= self.max_entries:
                break

            if pattern not in self.patterns:
                # Find next available code
                code = len(self.patterns) + 1
                self.patterns[pattern] = code
                self.reverse_patterns[code] = pattern

    def compress(self, text: str) -> Tuple[bytes, List[int]]:
        """
        Compress text using dictionary.

        Args:
            text: Text to compress

        Returns:
            Tuple of (compressed bytes, list of dictionary codes used)
        """
        if not text:
            return b"", []

        # Find and replace patterns
        result = bytearray()
        codes_used = []
        i = 0

        while i < len(text):
            matched = False

            # Try longest patterns first (greedy matching)
            for pattern_len in range(20, 2, -1):
                if i + pattern_len > len(text):
                    continue

                chunk = text[i:i+pattern_len]

                if chunk in self.patterns:
                    # Encode as single byte
                    code = self.patterns[chunk]
                    result.append(code)
                    codes_used.append(code)
                    i += pattern_len
                    matched = True
                    break

            if not matched:
                # No pattern match, keep original
                result.append(ord(text[i]))
                i += 1

        return bytes(result), codes_used

    def decompress(self, compressed: bytes) -> str:
        """
        Decompress text using dictionary.

        Args:
            compressed: Compressed bytes

        Returns:
            Decompressed text
        """
        result = []
        i = 0

        while i < len(compressed):
            code = compressed[i]

            if code in self.reverse_patterns:
                # Dictionary code
                result.append(self.reverse_patterns[code])
            else:
                # Literal byte
                result.append(chr(code))

            i += 1

        return ''.join(result)

    def get_stats(self) -> Dict:
        """
        Get dictionary statistics.

        Returns:
            Dictionary with stats
        """
        total_pattern_chars = sum(len(p) for p in self.patterns.keys())
        avg_pattern_len = total_pattern_chars / len(self.patterns) if self.patterns else 0

        return {
            'total_entries': len(self.patterns),
            'total_pattern_chars': total_pattern_chars,
            'avg_pattern_length': avg_pattern_len,
            'most_common_patterns': self.frequencies.most_common(10)
        }

    def save(self, path) -> None:
        """Save dictionary to file."""
        import pickle

        data = {
            'patterns': self.patterns,
            'reverse_patterns': self.reverse_patterns,
            'frequencies': dict(self.frequencies),
            'max_entries': self.max_entries
        }

        with open(path, 'wb') as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path) -> 'CodePatternDictionary':
        """Load dictionary from file."""
        import pickle

        with open(path, 'rb') as f:
            data = pickle.load(f)

        obj = cls(max_entries=data['max_entries'])
        obj.patterns = data['patterns']
        obj.reverse_patterns = data['reverse_patterns']
        obj.frequencies = Counter(data['frequencies'])

        return obj


def estimate_compression_ratio(code: str, dictionary: CodePatternDictionary) -> Dict:
    """
    Estimate compression ratio for code using dictionary.

    Args:
        code: Code to analyze
        dictionary: Pattern dictionary

    Returns:
        Dictionary with compression estimates
    """
    compressed, codes_used = dictionary.compress(code)

    original_size = len(code)
    compressed_size = len(compressed)

    if compressed_size == 0:
        return {
            'compression_ratio': 1.0,
            'savings_percent': 0.0,
            'original_size': original_size,
            'compressed_size': compressed_size
        }

    compression_ratio = original_size / compressed_size
    savings_percent = ((original_size - compressed_size) / original_size) * 100

    return {
        'compression_ratio': compression_ratio,
        'savings_percent': savings_percent,
        'original_size': original_size,
        'compressed_size': compressed_size,
        'patterns_used': len(codes_used)
    }


# Convenience functions

def create_default_dictionary() -> CodePatternDictionary:
    """Create dictionary with default patterns."""
    return CodePatternDictionary()


def learn_dictionary_from_files(
    file_paths: List,
    max_entries: int = 256
) -> CodePatternDictionary:
    """
    Learn compression dictionary from code files.

    Args:
        file_paths: List of file paths to learn from
        max_entries: Maximum dictionary entries

    Returns:
        Trained CodePatternDictionary
    """
    dictionary = CodePatternDictionary(max_entries=max_entries)

    for file_path in file_paths:
        try:
            code = file_path.read_text(errors='ignore')
            dictionary.learn_from_code(code)
        except Exception:
            pass

    return dictionary
