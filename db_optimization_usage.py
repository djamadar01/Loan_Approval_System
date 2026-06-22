"""
Integration guide and usage examples for db_optimization.py

Demonstrates how to integrate database optimization features with existing db.py
"""

from db import Database, ApplicationRecord, get_db, init_db
from db_optimization import (
    DatabaseOptimizer,
    IndexOptimizationRegistry,
    QueryOptimizationProfile,
    ConnectionPoolConfig,
    LazyLoader,
    PaginationHelper,
    optimize_existing_database,
    apply_optimization_pragmas,
    get_pagination_helper,
    get_lazy_loader
)
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE 1: Basic Optimization Setup
# ============================================================================

def example_basic_optimization():
    """Initialize database with all optimizations applied."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Optimization Setup")
    print("="*70)

    # Initialize database
    db = get_db()

    # Apply optimization pragmas to connection pool
    print("\n1. Applying optimization pragmas...")
    apply_optimization_pragmas(db)
    print("   ✓ Pragmas applied (WAL mode, better cache settings, etc.)")

    # Optimize indexes
    print("\n2. Creating all optimization indexes...")
    with db.pool.get_connection(write=True) as conn:
        optimizer = DatabaseOptimizer(conn)
        results = optimizer.optimize_indexes()
        for idx_name, success in results["results"].items():
            status = "✓" if success else "✗"
            print(f"   {status} {idx_name}")

    print("\n3. Index recommendations:")
    with db.pool.get_connection(write=False) as conn:
        optimizer = DatabaseOptimizer(conn)
        for idx in optimizer.index_registry.get_all_indexes():
            print(f"   • {idx.name}: {idx.description}")


# ============================================================================
# EXAMPLE 2: Query Optimization and Performance Analysis
# ============================================================================

def example_query_optimization():
    """Analyze and optimize common queries."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Query Optimization and Performance Analysis")
    print("="*70)

    db = get_db()

    with db.pool.get_connection(write=False) as conn:
        optimizer = DatabaseOptimizer(conn)
        query_profile = optimizer.query_profile

        # Analyze common query patterns
        queries = [
            ("SELECT * FROM applications WHERE status = ?", ["interview"]),
            ("SELECT * FROM applications WHERE company_name LIKE ?", ["%Tech%"]),
            ("SELECT * FROM applications ORDER BY created_at DESC", []),
        ]

        print("\n1. Query Execution Plan Analysis:")
        for query, params in queries:
            print(f"\n   Query: {query[:60]}...")
            analysis = query_profile.analyze_query(query, params)

            if "error" in analysis:
                print(f"   ✗ Error: {analysis['error']}")
            else:
                print(f"   ✓ Estimated rows: {analysis['estimated_rows']}")
                for rec in analysis.get("recommendations", []):
                    print(f"     {rec}")

        # Get overall recommendations
        print("\n2. Overall Database Recommendations:")
        recommendations = query_profile.get_recommendations()
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")

        # Index coverage report
        print("\n3. Current Index Coverage:")
        coverage = query_profile.get_index_coverage()
        print(f"   Total indexes: {coverage['total_indexes']}")
        for table, indexes in coverage["by_table"].items():
            print(f"   • {table}: {len(indexes)} indexes")
            for idx in indexes:
                print(f"     - {idx}")


# ============================================================================
# EXAMPLE 3: Connection Pool Configuration
# ============================================================================

def example_connection_pooling():
    """Demonstrate connection pool configuration and monitoring."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Connection Pool Configuration and Monitoring")
    print("="*70)

    db = get_db()
    pool_config = ConnectionPoolConfig()

    print("\n1. Pool Configuration Settings:")
    settings = pool_config.settings
    print(f"   Pool Size: {settings.pool_size}")
    print(f"   Timeout: {settings.timeout}s")
    print(f"   Journal Mode: {settings.journal_mode}")
    print(f"   Synchronous Mode: {settings.synchronous}")
    print(f"   Cache Size: {settings.cache_size} pages")
    print(f"   Temp Store: {settings.temp_store}")
    print(f"   Query Timeout: {settings.query_timeout}ms")

    print("\n2. Optimization Pragmas to Apply:")
    pragmas = pool_config.get_optimized_pragmas()
    for pragma, value in pragmas:
        print(f"   {pragma} = {value}")

    # Simulate usage
    print("\n3. Simulating Connection Usage Statistics:")
    for i in range(5):
        pool_config.record_acquisition()
        pool_config.record_query(15 + i * 10)  # Simulate query times
        pool_config.record_release()

    stats = pool_config.get_stats()
    print(f"   Total Acquired: {stats['total_acquired']}")
    print(f"   Total Queries: {stats['total_queries']}")
    print(f"   Slow Queries: {stats['slow_queries']}")
    print(f"   Peak Connections: {stats['peak_connections']}")


# ============================================================================
# EXAMPLE 4: Lazy Loading for Large Datasets
# ============================================================================

def example_lazy_loading():
    """Demonstrate lazy loading for memory-efficient data retrieval."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Lazy Loading for Large Datasets")
    print("="*70)

    db = get_db()

    # First, add some test data if database is empty
    stats = db.get_statistics()
    if stats["total_applications"] == 0:
        print("\n0. Adding test data...")
        for i in range(100):
            record = ApplicationRecord(
                job_title=f"Position {i}",
                company_name=f"Company {i % 10}",
                status="applied" if i % 3 == 0 else "interview",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            db.create_application(record)
        print("   ✓ Added 100 test records")

    with db.pool.get_connection(write=False) as conn:
        lazy_loader = LazyLoader(conn, batch_size=10)

        print("\n1. Lazy Loading with Batch Processing:")
        query = "SELECT * FROM applications ORDER BY id"
        batch_num = 0
        total_rows = 0

        for batch in lazy_loader.lazy_query(query):
            batch_num += 1
            total_rows += len(batch)
            print(f"   Batch {batch_num}: {len(batch)} rows (Total: {total_rows})")
            if batch_num >= 3:  # Show first 3 batches
                break

        print(f"   (... processing would continue ...)")

        print("\n2. Row-by-Row Iterator (Memory Efficient):")
        count = 0
        for row in lazy_loader.lazy_iterator(query):
            count += 1
            if count <= 3:
                print(f"   Row {count}: {row['company_name']} - {row['job_title']}")
            if count >= 10:
                print(f"   (... {total_rows - 10} more rows ...)")
                break

        print("\n3. Stream to File:")
        filepath = "/tmp/applications_export.txt"
        row_count = lazy_loader.stream_to_file(
            query,
            filepath,
            format_func=lambda r: f"{r['company_name']}: {r['job_title']}"
        )
        print(f"   ✓ Streamed {row_count} rows to {filepath}")


# ============================================================================
# EXAMPLE 5: Pagination with Efficiency Metrics
# ============================================================================

def example_pagination():
    """Demonstrate pagination with performance metrics."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Pagination with Efficiency Metrics")
    print("="*70)

    db = get_db()

    with db.pool.get_connection(write=False) as conn:
        pagination = PaginationHelper(conn)

        # Offset-based pagination
        print("\n1. Offset-Based Pagination (Traditional):")
        query = "SELECT * FROM applications"
        count_query = "SELECT COUNT(*) FROM applications"
        params = []

        page_result = pagination.paginate(
            query=query,
            count_query=count_query,
            params=params,
            page=1,
            page_size=10,
            order_by="created_at DESC"
        )

        info = page_result.get_info()
        print(f"   Page: {info['page']} of {info['total_pages']}")
        print(f"   Items: {info['items_in_page']}/{info['total_items']}")
        print(f"   Query Time: {info['query_time_ms']:.2f}ms")
        print(f"   Has Next: {info['has_next']}")
        print(f"   Has Previous: {info['has_previous']}")

        print("\n2. Cursor-Based Pagination (Efficient for Large Sets):")
        cursor_result = pagination.cursor_paginate(
            query="SELECT * FROM applications WHERE 1=1",
            params=[],
            cursor_column="id",
            page_size=10
        )

        info = cursor_result.get_info()
        print(f"   Items: {info['items_in_page']}")
        print(f"   Query Time: {info['query_time_ms']:.2f}ms")
        print(f"   Has Next: {info['has_next']}")
        if hasattr(cursor_result, 'next_cursor') and cursor_result.next_cursor:
            print(f"   Next Cursor: {cursor_result.next_cursor}")

        print("\n3. Filtered Pagination (Status = 'interview'):")
        filtered_result = pagination.paginate(
            query="SELECT * FROM applications WHERE status = ?",
            count_query="SELECT COUNT(*) FROM applications WHERE status = ?",
            params=["interview"],
            page=1,
            page_size=5
        )

        info = filtered_result.get_info()
        print(f"   Status: interview")
        print(f"   Results: {info['items_in_page']}/{info['total_items']}")
        print(f"   Total Pages: {info['total_pages']}")


# ============================================================================
# EXAMPLE 6: Complete Optimization Report
# ============================================================================

def example_optimization_report():
    """Generate and display complete optimization report."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Complete Optimization Report")
    print("="*70)

    db = get_db()

    print("\nGenerating comprehensive optimization report...")
    report = optimize_existing_database(db)

    print("\n1. INDEX OPTIMIZATION:")
    for idx_name, success in report["index_optimization"]["results"].items():
        status = "✓ Created" if success else "⚠ Exists/Failed"
        print(f"   {status}: {idx_name}")

    print("\n2. INDEX COVERAGE:")
    coverage = report["performance_analysis"]["index_coverage"]
    print(f"   Total indexes: {coverage['total_indexes']}")
    for table, indexes in coverage["by_table"].items():
        print(f"   Table '{table}': {len(indexes)} indexes")

    print("\n3. RECOMMENDATIONS:")
    recommendations = report["performance_analysis"]["recommendations"]
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")

    print("\n4. POOL CONFIGURATION:")
    pool_stats = report["performance_analysis"]["pool_stats"]
    settings = pool_stats["settings"]
    print(f"   Pool Size: {settings['pool_size']}")
    print(f"   Journal Mode: {settings['journal_mode']}")
    print(f"   Synchronous: {settings['synchronous']}")
    print(f"   Cache Size: {settings['cache_size']}")

    print("\n5. REGISTERED INDEXES:")
    indexes = report["index_registry"]["indexes"]
    for idx in indexes:
        print(f"   • {idx['name']}")
        print(f"     Columns: {', '.join(idx['columns'])}")
        print(f"     Purpose: {idx['description']}")


# ============================================================================
# EXAMPLE 7: Practical Integration in Application
# ============================================================================

def example_practical_integration():
    """Show practical integration patterns in an application."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Practical Integration Patterns")
    print("="*70)

    db = get_db()

    # Pattern 1: Efficient list retrieval with pagination
    print("\n1. Pattern: Efficient List Retrieval")
    print("   Code:")
    print("""
    pagination = get_pagination_helper(db)
    result = pagination.paginate(
        query="SELECT * FROM applications WHERE status = ?",
        count_query="SELECT COUNT(*) FROM applications WHERE status = ?",
        params=["interview"],
        page=1,
        page_size=20
    )
    print(f"Page {result.page_number} of {result.total_pages}")
    for item in result.items:
        print(f"  {item['company_name']}: {item['job_title']}")
    """)

    # Pattern 2: Memory-efficient export
    print("\n2. Pattern: Memory-Efficient Export")
    print("   Code:")
    print("""
    lazy_loader = get_lazy_loader(db, batch_size=1000)
    lazy_loader.stream_to_file(
        query="SELECT * FROM applications",
        filepath="export.jsonl",
        format_func=lambda r: json.dumps(dict(r))
    )
    """)

    # Pattern 3: Query optimization
    print("\n3. Pattern: Query Optimization Analysis")
    print("   Code:")
    print("""
    with db.pool.get_connection() as conn:
        optimizer = DatabaseOptimizer(conn)
        analysis = optimizer.query_profile.analyze_query(
            "SELECT * FROM applications WHERE status = ? AND company_name LIKE ?",
            ["interview", "%Tech%"]
        )
        print(f"Estimated rows: {analysis['estimated_rows']}")
        for rec in analysis['recommendations']:
            print(f"Optimization: {rec}")
    """)

    # Pattern 4: Lazy loading large datasets
    print("\n4. Pattern: Lazy Loading Large Datasets")
    print("   Code:")
    print("""
    lazy_loader = get_lazy_loader(db, batch_size=500)
    with lazy_loader.lazy_query("SELECT * FROM applications") as batches:
        for batch in batches:
            process_batch(batch)  # Process in chunks
    """)


# ============================================================================
# Main execution
# ============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*70)
    print("DATABASE OPTIMIZATION MODULE - USAGE EXAMPLES")
    print("="*70)

    try:
        # Run examples
        example_basic_optimization()
        example_query_optimization()
        example_connection_pooling()
        example_lazy_loading()
        example_pagination()
        example_optimization_report()
        example_practical_integration()

        print("\n" + "="*70)
        print("✓ All examples completed successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
