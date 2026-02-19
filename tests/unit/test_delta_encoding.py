"""
Test delta encoding implementation.
"""

from palace.core.delta_encoding import (
    DeltaCompressor,
    DeltaEncoder,
    estimate_savings,
    apply_delta_compression
)


def test_delta_encoder():
    """Test basic delta encoding."""
    encoder = DeltaEncoder()

    # Test identical
    base = "abc123def456"
    target = "abc123def456"
    delta = encoder.encode_delta(base, target)
    decoded = encoder.decode_delta(base, delta)
    assert decoded == target

    # Test small difference
    base = "abc123def456"
    target = "abc123xyz456"
    delta = encoder.encode_delta(base, target)
    decoded = encoder.decode_delta(base, delta)
    assert decoded == target

    # Test completely different
    base = "abc123"
    target = "xyz789"
    delta = encoder.encode_delta(base, target)
    decoded = encoder.decode_delta(base, delta)
    assert decoded == target

    print("✅ Delta encoding tests passed")


def test_delta_compressor():
    """Test clustering and compression."""
    compressor = DeltaCompressor(similarity_threshold=0.7)

    # Add similar fingerprints (valid hex only: 0-9, a-f)
    fp1 = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    fp2 = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b3"  # 1 char diff
    fp3 = "f9e8d7c6b5a4f9e8d7c6b5a4f9e8d7c6b5a4f9e8d7c6b5a4f9e8d7c6b5a4f9"  # Completely different

    compressor.add_fingerprint("file1.py", fp1)
    compressor.add_fingerprint("file2.py", fp2)
    compressor.add_fingerprint("file3.py", fp3)

    stats = compressor.get_compression_stats()

    assert stats['total_artifacts'] == 3
    assert stats['total_clusters'] >= 1
    assert stats['compression_ratio'] > 1.0

    print(f"✅ Delta compressor tests passed")
    print(f"   Compression ratio: {stats['compression_ratio']:.2f}×")
    print(f"   Savings: {stats['savings_bytes']:,} bytes")


def test_estimate_savings():
    """Test savings estimation."""
    # High similarity
    result = estimate_savings(10000, avg_similarity=0.8)
    assert result['recommended'] == True
    assert result['savings_percent'] > 20

    # Low similarity
    result = estimate_savings(10000, avg_similarity=0.3)
    assert result['recommended'] == False
    assert result['savings_percent'] < 10

    print("✅ Savings estimation tests passed")


if __name__ == '__main__':
    test_delta_encoder()
    test_delta_compressor()
    test_estimate_savings()
    print("\n✅ All delta encoding tests passed!")
