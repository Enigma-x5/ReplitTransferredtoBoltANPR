#!/bin/bash
set -e

echo "🚀 ANPR City API Bootstrap Script"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.template .env

    # Generate JWT secret
    JWT_SECRET=$(openssl rand -base64 32)

    # Update JWT_SECRET in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" .env
    else
        sed -i "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" .env
    fi

    echo "✅ .env created with secure JWT_SECRET"
    echo "⚠️  Please review and update other values in .env"
    echo ""
else
    echo "✅ .env already exists"

    # Check if JWT_SECRET needs to be generated
    if grep -q "JWT_SECRET=CHANGE_ME" .env; then
        echo "📝 Generating JWT_SECRET..."
        JWT_SECRET=$(openssl rand -base64 32)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" .env
        else
            sed -i "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" .env
        fi
        echo "✅ JWT_SECRET generated"
    fi
    echo ""
fi

# Check MODE
MODE=$(grep "^MODE=" .env | cut -d'=' -f2)

echo "🔧 Detected MODE: $MODE"
echo ""

if [ "$MODE" == "selfhost" ]; then
    echo "🐳 Starting self-hosted stack..."
    docker-compose up -d postgres redis minio

    echo "⏳ Waiting for services to be ready..."
    sleep 10

    echo "📊 Running database migrations..."
    # Check if migrations dir exists
    if [ -d "migrations" ]; then
        docker-compose run --rm api bash -c "psql \$DATABASE_URL -f /app/migrations/001_initial_schema.sql 2>/dev/null" || echo "   (Migration may have already been applied)"
    fi

    echo "👤 Creating admin user..."
    docker-compose run --rm api python -c "
import asyncio
from src.database import AsyncSessionLocal
from src.models.user import User
from src.auth import get_password_hash
from src.config import settings
from sqlalchemy import select

async def create_admin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            admin_user = User(
                email=settings.ADMIN_EMAIL,
                username=settings.ADMIN_USERNAME,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_active=True,
                role='admin'
            )
            db.add(admin_user)
            await db.commit()
            print('   ✅ Admin user created')
        else:
            print('   ✅ Admin user already exists')

asyncio.run(create_admin())
" 2>/dev/null || echo "   (Admin creation skipped - will be created on first API start)"

    echo ""
    echo "✅ Self-hosted infrastructure ready!"
    echo ""
    echo "Next steps:"
    echo "  1. docker-compose up -d api worker"
    echo "  2. Open http://localhost:8000/docs"
    echo "  3. Login with ${ADMIN_EMAIL:-admin@example.com} / ${ADMIN_PASSWORD:-changeme123}"

elif [ "$MODE" == "supabase" ]; then
    echo "☁️  Supabase mode detected"
    echo ""
    echo "Please complete Supabase setup manually:"
    echo "  1. Create Supabase project at https://supabase.com"
    echo "  2. Update SUPABASE_* variables in .env"
    echo "  3. Run migrations/001_initial_schema.sql in Supabase SQL editor"
    echo "  4. Create storage buckets: anpr-uploads, anpr-crops"
    echo ""
    echo "See SUPABASE_SETUP.md for detailed instructions"
    echo ""
    echo "After Supabase setup, run:"
    echo "  docker-compose -f docker-compose.supabase.yml up -d"

else
    echo "❌ Unknown MODE: $MODE"
    echo "Please set MODE=supabase or MODE=selfhost in .env"
    exit 1
fi

echo ""
echo "📚 Documentation:"
echo "  - README.md - Overview and setup"
echo "  - DEVELOPER_HANDOFF.md - Technical details"
echo "  - API_QUICK_REFERENCE.md - API examples"
echo "  - SUPABASE_SETUP.md - Supabase configuration"
echo ""
echo "🎉 Bootstrap complete!"
