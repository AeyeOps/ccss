# Search Performance Research Plan

## Overview

This document outlines a research plan for improving search performance in ccss (Claude Code Session Search). The goal is to identify optimization opportunities and provide actionable recommendations.

## Current Architecture

### Index Structure
- **Database**: SQLite with FTS5 virtual table
- **Schema**: External content table pattern (messages_fts references messages table)
- **Tokenizer**: Porter stemmer with unicode61
- **Location**: `~/.cache/ccss/sessions.db`

### Search Flow
1. User types query
2. Query transformed to FTS5 syntax (prefix matching added)
3. FTS5 MATCH query executed
4. Results joined with sessions table for metadata
5. Results grouped by session, sorted by last_modified
6. Top 50 results returned

## Baseline Metrics (To Be Collected)

### Metrics to Capture
- Cold start time (first launch with empty cache)
- Warm start time (subsequent launches)
- Index build time for N sessions
- Query response time for various query types:
  - Single word search
  - Multi-word search
  - Phrase search
  - Prefix search
- Memory usage during indexing
- Database file size vs session file size ratio

### Profiling Tools
- `cProfile` for Python-level profiling
- `sqlite3.set_trace_callback()` for query timing
- `time.perf_counter()` for wall-clock measurements

## Investigation Areas

### 1. Query Optimization

**Current Limitations**:
- bm25() ranking disabled due to external content table
- Results sorted by recency only, not relevance
- No query caching

**Potential Improvements**:

#### A. Enable BM25 Ranking
- Switch from external content to regular FTS5 table
- Trade-off: Larger index (stores content twice)
- Benchmark: Compare index size and query speed

#### B. Query Result Caching
- Cache recent query results in memory
- LRU cache with configurable size
- Invalidate on index update
- Trade-off: Memory usage vs speed

#### C. Query Optimization
- Pre-compile common query patterns
- Batch similar queries
- Use FTS5 column filters if applicable

### 2. Index Structure Improvements

**Current State**:
- Single content column indexed
- External content table (space efficient)
- Porter stemmer only

**Potential Improvements**:

#### A. Trigram Tokenizer
- Add trigram index for better partial matching
- Trade-off: Larger index, but faster substring search
- Benchmark: Compare query times for partial matches

#### B. Column-Based Indexing
- Separate columns for user vs assistant messages
- Enable column-weighted ranking
- Trade-off: Schema complexity

#### C. Denormalization
- Store session metadata in FTS table
- Eliminate JOIN in search query
- Trade-off: Data duplication

### 3. Caching Strategies

**Current State**:
- No caching of query results
- No caching of session previews
- Full preview loaded on each highlight

**Potential Improvements**:

#### A. Session Preview Cache
- Cache last N session previews in memory
- Significant for users browsing results
- LRU eviction policy

#### B. SQLite Configuration
- Enable WAL mode for better concurrent reads
- Tune page cache size
- Consider mmap for large databases

```sql
PRAGMA journal_mode=WAL;
PRAGMA cache_size=-64000;  -- 64MB cache
PRAGMA mmap_size=268435456;  -- 256MB mmap
```

### 4. Background Indexing

**Current State**:
- Blocking index build on startup
- User waits for indexing before search

**Potential Improvements**:

#### A. Incremental Background Updates
- Use file watcher (watchdog) for new/modified files
- Index changes in background thread
- Update UI when new sessions available

#### B. Lazy Indexing
- Index only on first search
- Show "indexing..." status during search if needed
- Cache indexed sessions count

#### C. Subprocess Indexing
- Run indexer in separate process
- Communicate via IPC or shared database
- Trade-off: Process management complexity

## Benchmark Plan

### Test Dataset
- Small: 50 sessions, ~500 messages
- Medium: 200 sessions, ~2000 messages
- Large: 500+ sessions, ~5000+ messages

### Test Queries
1. Single common word: "function"
2. Single rare word: "kubernetes"
3. Two-word query: "react typescript"
4. Phrase search: "error handling"
5. Prefix search: "migrat*"
6. No results query: "xyznonexistent"

### Metrics Collection Script

```python
import cProfile
import pstats
import time
from ccss.indexer import build_index, get_db_connection
from ccss.search import search_sessions

def benchmark_search():
    conn = get_db_connection()

    queries = [
        "function",
        "kubernetes",
        "react typescript",
        "error handling",
        "migrat*",
        "xyznonexistent"
    ]

    results = {}
    for query in queries:
        times = []
        for _ in range(10):
            start = time.perf_counter()
            search_sessions(conn, query)
            times.append(time.perf_counter() - start)

        results[query] = {
            "mean_ms": sum(times) / len(times) * 1000,
            "min_ms": min(times) * 1000,
            "max_ms": max(times) * 1000
        }

    return results

if __name__ == "__main__":
    # Run with profiling
    profiler = cProfile.Profile()
    profiler.enable()

    results = benchmark_search()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

    print("\nQuery Benchmark Results:")
    for query, data in results.items():
        print(f"  {query}: {data['mean_ms']:.2f}ms (min: {data['min_ms']:.2f}, max: {data['max_ms']:.2f})")
```

## Recommended Priority

1. **High Impact, Low Effort**:
   - Enable WAL mode (single PRAGMA)
   - Add session preview caching
   - Tune SQLite cache size

2. **Medium Impact, Medium Effort**:
   - Implement query result caching
   - Add file watcher for background updates

3. **High Impact, High Effort**:
   - Switch to non-external content FTS5 for bm25()
   - Implement trigram tokenizer

## Success Criteria

- Query response time < 100ms for 95th percentile
- Index build time < 30s for 500 sessions
- Memory usage < 100MB during normal operation
- No perceptible lag when typing search queries

## Next Steps

1. Run baseline benchmarks with current implementation
2. Implement WAL mode and measure improvement
3. Add session preview caching
4. Re-benchmark and document findings
5. Prioritize remaining optimizations based on data

---

*This research plan will be updated with actual benchmark data as measurements are collected.*
