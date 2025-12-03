#!/usr/bin/env python3
"""
Migration script to create tables in the connected database.
"""
import asyncio
import os
import ssl
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

async def run_migrations():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    print(f"Connecting to database...")
    
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    has_ssl = 'sslmode' in query_params or 'ssl' in query_params
    
    new_query = {k: v[0] if len(v) == 1 else v for k, v in query_params.items() if k not in ['sslmode', 'ssl']}
    new_query_string = urlencode(new_query) if new_query else ''
    
    if parsed.scheme == 'postgresql':
        new_scheme = 'postgresql+asyncpg'
    elif parsed.scheme == 'postgres':
        new_scheme = 'postgresql+asyncpg'
    else:
        new_scheme = parsed.scheme
    
    clean_url = urlunparse((
        new_scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query_string,
        parsed.fragment
    ))
    
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    
    connect_args = {}
    if has_ssl:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args['ssl'] = ssl_context
    
    engine = create_async_engine(clean_url, echo=False, connect_args=connect_args)
    
    migration_file = Path("migrations/001_initial_schema.sql")
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    migration_sql = migration_file.read_text()
    
    statements = []
    current_statement = []
    in_function = False
    in_comment_block = False
    
    for line in migration_sql.split('\n'):
        stripped = line.strip()
        
        if stripped.startswith('/*'):
            in_comment_block = True
            continue
        if '*/' in stripped:
            in_comment_block = False
            continue
        if in_comment_block:
            continue
        if stripped.startswith('--'):
            continue
        
        if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
            in_function = True
        
        current_statement.append(line)
        
        if in_function:
            if '$$ LANGUAGE' in line or stripped.endswith('$$;') or 'LANGUAGE plpgsql;' in line:
                in_function = False
                stmt = '\n'.join(current_statement).strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []
        elif stripped.endswith(';') and not in_function:
            stmt = '\n'.join(current_statement).strip()
            if stmt and not stmt.startswith('--') and not stmt.startswith('/*'):
                statements.append(stmt)
            current_statement = []
    
    print(f"Found {len(statements)} SQL statements to execute")
    
    async with engine.begin() as conn:
        for i, stmt in enumerate(statements, 1):
            stmt_preview = stmt[:80].replace('\n', ' ')
            if len(stmt) > 80:
                stmt_preview += "..."
            print(f"[{i}/{len(statements)}] Executing: {stmt_preview}")
            
            try:
                await conn.execute(text(stmt))
                print(f"    OK")
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    print(f"    SKIP (already exists)")
                else:
                    print(f"    ERROR: {error_msg[:200]}")
    
    print("\nMigration completed!")
    return True

if __name__ == "__main__":
    asyncio.run(run_migrations())
