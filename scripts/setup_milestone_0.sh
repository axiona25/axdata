#!/bin/bash
# Setup script for Milestone 0 - Bootstrap & Infrastruttura

set -e

echo "🚀 Setting up Milestone 0: Bootstrap & Infrastruttura"
echo "====================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Start Docker services
echo ""
echo "1. Starting Docker services..."
cd infra
docker compose up -d
echo -e "${GREEN}✓ Docker services started${NC}"

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# 2. Check services are running
echo ""
echo "2. Verifying services..."
docker compose ps

# 3. Setup MinIO bucket
echo ""
echo "3. Setting up MinIO bucket..."
# MinIO bucket will be created on first use, but we can verify connection
echo -e "${YELLOW}Note: MinIO bucket will be created automatically on first use${NC}"

# 4. Install Python dependencies (if virtualenv exists)
echo ""
echo "4. Python dependencies..."
if [ -d "../apps/backend" ]; then
    echo "Backend requirements.txt found"
    echo -e "${YELLOW}Run: cd apps/backend && pip install -r requirements.txt${NC}"
fi
if [ -d "../apps/collector" ]; then
    echo "Collector requirements.txt found"
    echo -e "${YELLOW}Run: cd apps/collector && pip install -r requirements.txt${NC}"
fi

echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Install Python dependencies:"
echo "   cd apps/backend && pip install -r requirements.txt"
echo "   cd apps/collector && pip install -r requirements.txt"
echo ""
echo "2. Start backend:"
echo "   cd apps/backend && python run.py"
echo ""
echo "3. Start collector (in another terminal):"
echo "   cd apps/collector && python run.py"
echo ""
echo "4. Run tests:"
echo "   ./scripts/test_milestone_0.sh"

