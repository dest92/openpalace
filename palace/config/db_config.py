"""Optimal database configuration settings for Palace Mental."""

# KuzuDB optimal configuration
# Based on KuzuDB 0.5.0 Database() parameters (current installed version)
KUZU_OPTIMAL_CONFIG = {
    # Buffer pool size in bytes (default: ~80% of system memory)
    # 1GB buffer pool for large datasets
    'buffer_pool_size': 1073741824,

    # Maximum number of threads for query execution
    # Set to number of CPU cores for optimal parallelism
    'max_num_threads': 8,

    # Maximum database size in bytes (default: 8TB)
    # MUST be a power of 2 for KuzuDB 0.5.0+
    # 16GB limit for controlled growth
    'max_db_size': 17179869184,  # 16GB (2^34)

    # Enable database compression (default: True)
    'compression': True,
}

# SQLite+vec optimal configuration
SQLITE_OPTIMAL_PRAGMAS = {
    # WAL mode for better concurrency
    'journal_mode': 'WAL',

    # Synchronous mode - balance safety/speed
    'synchronous': 'NORMAL',

    # Aggressive caching
    'cache_size': -1000000,  # 1GB cache (negative value means KB)
    'mmap_size': 1073741824,  # 1GB mmap

    # Temp store in memory
    'temp_store': 'MEMORY',

    # Page size optimal for vectors
    'page_size': 4096,

    # Locking mode
    'locking_mode': 'NORMAL',

    # Optimization settings
    'optimize': '0x10002',  # OPTIMIZE flag
}

# Performance tuning settings
PERFORMANCE_CONFIG = {
    # Batch sizes for bulk operations
    'batch_size_nodes': 100,
    'batch_size_edges': 500,
    'batch_size_embeddings': 1000,

    # Parallelism
    'max_workers_ingestion': None,  # None = cpu_count()
    'max_workers_processing': None,

    # Cache sizes
    'query_cache_size': 1024,
    'edge_weight_cache_size': 2048,
    'artifact_lookup_cache_size': 4096,

    # Thresholds for optimizations
    'vectorization_threshold': 5,  # Use vectorized ops for n >= 5
    'parallel_threshold': 10,  # Use parallel processing for n >= 10
    'large_file_threshold_mb': 50,  # Files larger than this are processed sequentially
}


def get_kuzu_config() -> dict:
    """Get KuzuDB configuration as dict for Database() constructor."""
    return KUZU_OPTIMAL_CONFIG.copy()


def get_sqlite_pragmas() -> list:
    """Get SQLite pragmas as list of PRAGMA statements."""
    return [
        f"PRAGMA {key} = {value};"
        for key, value in SQLITE_OPTIMAL_PRAGMAS.items()
    ]
