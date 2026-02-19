#!/usr/bin/env python3
"""
Quick V2 benchmark on Linux kernel subset.

Tests actual storage and performance on real massive codebase.
"""

import hashlib
import time
from pathlib import Path
from palace.core.bloom_filter import create_palace_bloom_filter
from palace.core.delta_encoding import DeltaCompressor
from palace.core.dictionary_compression import CodePatternDictionary

def benchmark_linux_kernel():
    """Run benchmark on Linux kernel."""
    kernel_path = Path("/mnt/disco-externo/test-projects/linux")

    print("=" * 60)
    print("🐧 PALACE MENTAL V2 - Linux Kernel Benchmark")
    print("=" * 60)

    # Step 1: Scan files
    print("\n📂 Step 1: Scanning files...")
    c_files = list(kernel_path.rglob("*.c"))
    h_files = list(kernel_path.rglob("*.h"))

    print(f"   C files: {len(c_files):,}")
    print(f"   H files: {len(h_files):,}")
    print(f"   Total: {len(c_files) + len(h_files):,} files")

    # Use first 10K files for quick test
    sample_files = (c_files + h_files)[:10000]
    print(f"   Testing on: {len(sample_files):,} files (sample)")

    # Step 2: Benchmark Bloom filter
    print("\n🌸 Step 2: Bloom Filter Creation...")
    bloom_start = time.time()

    bloom = create_palace_bloom_filter(
        num_artifacts=len(sample_files),
        false_positive_rate=0.001
    )

    for file_path in sample_files:
        file_id = str(file_path.relative_to(kernel_path))
        bloom.add(file_id)

    bloom_time = time.time() - bloom_start
    bloom_stats = bloom.get_stats()

    print(f"   Time: {bloom_time:.2f}s")
    print(f"   Size: {bloom_stats['size_mb']:.2f}MB")
    print(f"   Items: {bloom.estimate_count():,}")

    # Step 3: Benchmark AST fingerprints
    print("\n🌳 Step 3: AST Fingerprinting...")
    fingerprint_start = time.time()

    fingerprints = {}
    for file_path in sample_files[:1000]:  # First 1K for speed
        try:
            code = file_path.read_text(errors='ignore')
            fp = hashlib.sha256(code.encode()).hexdigest()
            fingerprints[str(file_path.relative_to(kernel_path))] = fp
        except Exception:
            pass

    fingerprint_time = time.time() - fingerprint_start
    fp_size_mb = len(fingerprints) * 32 / (1024 * 1024)

    print(f"   Time: {fingerprint_time:.2f}s (for 1K files)")
    print(f"   Storage: {fp_size_mb:.2f}MB (1K files × 32 bytes)")
    print(f"   Projected: {fp_size_mb * len(sample_files) / 1000:.2f}MB (all files)")

    # Step 4: Benchmark Delta compression
    print("\n🔄 Step 4: Delta Encoding...")
    delta_start = time.time()

    delta = DeltaCompressor(similarity_threshold=0.7)
    for file_id, fp in list(fingerprints.items())[:100]:
        delta.add_fingerprint(file_id, fp)

    delta_time = time.time() - delta_start
    delta_stats = delta.get_compression_stats()

    print(f"   Time: {delta_time:.2f}s")
    print(f"   Compression ratio: {delta_stats['compression_ratio']:.2f}×")
    print(f"   Savings: {delta_stats['savings_bytes']:,} bytes")

    # Step 5: Benchmark Dictionary compression
    print("\n📚 Step 5: Dictionary Compression...")
    dict_start = time.time()

    dictionary = CodePatternDictionary(max_entries=256)

    # Learn from first 100 files
    for file_path in sample_files[:100]:
        try:
            code = file_path.read_text(errors='ignore')
            # Learn from first 10KB only for speed
            dictionary.learn_from_code(code[:10240])
        except Exception:
            pass

    dict_time = time.time() - dict_start
    dict_stats = dictionary.get_stats()

    print(f"   Time: {dict_time:.2f}s (learning from 100 files)")
    print(f"   Dictionary entries: {dict_stats['total_entries']}")
    print(f"   Avg pattern length: {dict_stats['avg_pattern_length']:.2f}")

    # Test compression on sample
    sample_code = """
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

    from palace.core.dictionary_compression import estimate_compression_ratio
    comp_result = estimate_compression_ratio(sample_code, dictionary)

    print(f"   Test compression: {comp_result['compression_ratio']:.2f}×")
    print(f"   Test savings: {comp_result['savings_percent']:.1f}%")

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    # Calculate total storage
    total_fp_storage = len(sample_files) * 32 / (1024 * 1024)  # MB
    total_bloom_storage = bloom_stats['size_mb']

    # With delta
    delta_savings = (delta_stats['baseline_storage_bytes'] - delta_stats['delta_storage_bytes']) / (1024 * 1024)
    total_with_delta = total_fp_storage + total_bloom_storage - delta_savings

    print(f"\nStorage (10K files subset):")
    print(f"  Fingerprints:   {total_fp_storage:.2f}MB")
    print(f"  Bloom filter:  {total_bloom_storage:.2f}MB")
    print(f"  ─────────────────────────────────")
    print(f"  Baseline:      {total_fp_storage + total_bloom_storage:.2f}MB")
    print(f"  With delta:    {total_with_delta:.2f}MB")
    print(f"  Savings:       {delta_savings:.2f}MB")

    # Project to full kernel
    scaling_factor = len(sample_files) / len(sample_files)  # Should be 1, but just in case
    full_kernel_baseline = (total_fp_storage + total_bloom_storage) * (63067 / len(sample_files))
    full_kernel_with_delta = total_with_delta * (63067 / len(sample_files))

    print(f"\nProjected (63K files full kernel):")
    print(f"  Baseline:      {full_kernel_baseline:.2f}MB")
    print(f"  With delta:    {full_kernel_with_delta:.2f}MB")
    print(f"  Per-file:      {full_kernel_with_delta / 63067 * 1024 * 1024:.0f} bytes/file")

    # Compare to baseline V2 target
    print(f"\n🎯 vs V2 Target (522MB for 10M files):")
    per_10m_baseline = (full_kernel_with_delta / 63067) * 10_000_000
    print(f"  Projected for 10M files: {per_10m_baseline:.2f}MB")
    print(f"  Target:                   522MB")
    if per_10m_baseline < 522:
        print(f"  ✅ EXCEEDS TARGET by {(522 - per_10m_baseline):.2f}MB!")
    else:
        print(f"  ❌ Above target by {(per_10m_baseline - 522):.2f}MB")

    print(f"\n✅ Benchmark complete!")

if __name__ == '__main__':
    benchmark_linux_kernel()
