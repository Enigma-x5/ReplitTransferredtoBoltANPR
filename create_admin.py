import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from passlib.context import CryptContext
from src.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    database_url = os.getenv("DATABASE_URL")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    engine = create_async_engine(database_url)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == admin_email))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Admin user already exists: {admin_email}")
            return
        
        hashed_password = pwd_context.hash(admin_password)
        admin_user = User(
            email=admin_email,
            username=admin_username,
            hashed_password=hashed_password,
            role="admin",
        )
        db.add(admin_user)
        await db.commit()
        print(f"Admin user created: {admin_email} / {admin_username}")
        print(f"Password: {admin_password}")

if __name__ == "__main__":
    asyncio.run(create_admin_user())
