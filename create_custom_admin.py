#!/usr/bin/env python3
"""
Create a custom admin user in the database.
"""
import asyncio
import os
import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

async def create_admin_user():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    ADMIN_EMAIL = "admin@admin.com"
    ADMIN_PASSWORD = "Admin@123"
    ADMIN_USERNAME = "customadmin"
    
    print(f"Creating admin user: {ADMIN_EMAIL}")
    
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    has_ssl = 'sslmode' in query_params or 'ssl' in query_params
    
    new_query = {k: v[0] if len(v) == 1 else v for k, v in query_params.items() if k not in ['sslmode', 'ssl']}
    new_query_string = urlencode(new_query) if new_query else ''
    
    if parsed.scheme in ['postgresql', 'postgres']:
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
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(ADMIN_PASSWORD)
    
    print(f"Password hashed successfully")
    
    connect_args = {}
    if has_ssl:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args['ssl'] = ssl_context
    
    engine = create_async_engine(clean_url, echo=False, connect_args=connect_args)
    
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": ADMIN_EMAIL}
        )
        existing = result.fetchone()
        
        if existing:
            print(f"User {ADMIN_EMAIL} already exists, updating password...")
            await conn.execute(
                text("UPDATE users SET hashed_password = :password WHERE email = :email"),
                {"password": hashed_password, "email": ADMIN_EMAIL}
            )
            print(f"Password updated successfully!")
        else:
            print(f"Creating new admin user...")
            await conn.execute(
                text("""
                    INSERT INTO users (email, username, hashed_password, role, is_active)
                    VALUES (:email, :username, :password, 'admin', true)
                """),
                {"email": ADMIN_EMAIL, "username": ADMIN_USERNAME, "password": hashed_password}
            )
            print(f"Admin user created successfully!")
    
    print(f"\nAdmin user ready:")
    print(f"  Email: {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")
    return True

if __name__ == "__main__":
    asyncio.run(create_admin_user())
