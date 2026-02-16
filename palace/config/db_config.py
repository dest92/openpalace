"""Optimal database configuration settings for Palace Mental."""

# KuzuDB optimal configuration
# Based on KuzuDB 0.11.3 Database() parameters
KUZU_OPTIMAL_CONFIG = {
    # Buffer pool size in bytes (default: ~80% of system memory)
    # 1GB buffer pool for large datasets
    'buffer_pool_size': 1073741824,

    # Maximum number of threads for query execution
    # Set to number of CPU cores for optimal parallelism
    'max_num_threads': 8,

    # Maximum database size in bytes (default: 8TB)
    # 10GB limit for controlled growth
    'max_db_size': 10737418240,  # 10GB

    # Enable database compression (default: True)
    'compression': True,

    # Auto checkpoint after writes (default: True)
    'auto_checkpoint': True,

    # Checkpoint threshold in bytes (-1 = use default)
    'checkpoint_threshold': -1,
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
