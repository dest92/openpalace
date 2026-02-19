"""
Test dictionary compression implementation.
"""

from palace.core.dictionary_compression import (
    CodePatternDictionary,
    estimate_compression_ratio,
    create_default_dictionary,
    learn_dictionary_from_files
)
from pathlib import Path


def test_basic_compression():
    """Test basic dictionary compression."""
    dictionary = CodePatternDictionary()

    # Test compression of common patterns
    code = "def foo(): return True"
    compressed, codes = dictionary.compress(code)
    decompressed = dictionary.decompress(compressed)

    assert decompressed == code
    print("✅ Basic compression test passed")


def test_pattern_learning():
    """Test learning patterns from code."""
    dictionary = CodePatternDictionary()

    # Learn from Python code
    code = """
def function1():
    return True

def function2():
    return False

class MyClass:
    def method(self):
        pass

import os
import sys
"""

    dictionary.learn_from_code(code)
    stats = dictionary.get_stats()

    assert stats['total_entries'] >= 20  # Should have default patterns
    assert stats['avg_pattern_length'] > 0

    print(f"✅ Pattern learning test passed")
    print(f"   Dictionary entries: {stats['total_entries']}")
    print(f"   Avg pattern length: {stats['avg_pattern_length']:.2f}")


def test_compression_ratio():
    """Test compression ratio estimation."""
    dictionary = CodePatternDictionary()

    # Code with many repeated patterns
    code = """
def func1(): return True
def func2(): return False
def func3(): return None
class Class1: pass
class Class2: pass
import os
import sys
"""

    result = estimate_compression_ratio(code, dictionary)

    assert result['compression_ratio'] >= 1.0
    assert result['original_size'] > result['compressed_size']
    assert result['patterns_used'] > 0

    print(f"✅ Compression ratio test passed")
    print(f"   Ratio: {result['compression_ratio']:.2f}×")
    print(f"   Savings: {result['savings_percent']:.1f}%")


def test_roundtrip():
    """Test compress -> decompress roundtrip."""
    dictionary = CodePatternDictionary()

    test_cases = [
        "def hello(): return 'world'",
        "class Foo: def __init__(self): self.x = 1",
        "import os, sys",
        "if True: pass else: pass",
        "return None"
    ]

    for code in test_cases:
        compressed, _ = dictionary.compress(code)
        decompressed = dictionary.decompress(compressed)
        assert decompressed == code, f"Failed for: {code}"

    print("✅ Roundtrip test passed (5/5 cases)")


def test_default_dictionary():
    """Test default dictionary has common patterns."""
    dictionary = create_default_dictionary()

    stats = dictionary.get_stats()

    assert stats['total_entries'] >= 20

    # Check that common patterns exist
    compressed, _ = dictionary.compress("def ")
    assert len(compressed) <= 1  # Should be encoded as single byte

    compressed, _ = dictionary.compress("class ")
    assert len(compressed) <= 1

    print("✅ Default dictionary test passed")
    print(f"   Entries: {stats['total_entries']}")


if __name__ == '__main__':
    test_basic_compression()
    test_pattern_learning()
    test_compression_ratio()
    test_roundtrip()
    test_default_dictionary()
    print("\n✅ All dictionary compression tests passed!")
