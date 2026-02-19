#!/bin/bash
# Alternative installation script for Palace Mental V2
# Use this if poetry is taking too long

set -e

echo "🚀 Palace Mental V2 - Installation"
echo "=================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# Install mmh3 (only new dependency for V2)
echo ""
echo "📦 Installing mmh3 (for Bloom filter)..."
pip3 install mmh3 --user || { echo "❌ Failed to install mmh3"; exit 1; }

# Verify installation
echo ""
echo "✅ Verifying installation..."
python3 -c "import mmh3; print(f'mmh3 version: {mmh3.__version__}')" || { echo "❌ mmh3 import failed"; exit 1; }

# Test V2 demo
echo ""
echo "🧪 Testing V2 demo..."
PYTHONPATH=/home/ben10/palace2 python3 examples/v2_demo_simple.py || { echo "❌ Demo failed"; exit 1; }

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Run tests: python3 -m pytest tests/integration/test_v2_integration.py -v"
echo "  2. Try migration: python3 scripts/migrate_v1_to_v2.py --dry-run"
echo "  3. See quickstart: cat docs/V2_QUICKSTART.md"
