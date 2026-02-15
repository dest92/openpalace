#!/usr/bin/env python3
"""
Automated setup script for Palace Mental.
Installs dependencies and verifies installation.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and report success/failure."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main setup process."""
    print("🏛️ Palace Mental - Automated Setup")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)

    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Check if Poetry is installed
    poetry_check = subprocess.run(
        ["poetry", "--version"],
        capture_output=True
    )

    if poetry_check.returncode != 0:
        print("❌ Poetry not found")
        print("   Install from: https://python-poetry.org/docs/#installation")
        sys.exit(1)

    print("✅ Poetry is installed")

    # Install dependencies
    print("\n📦 Installing dependencies...")
    success = run_command(
        ["poetry", "install"],
        "Installing dependencies with Poetry"
    )

    if not success:
        print("\n⚠️  Poetry install failed. Trying pip install...")
        success = run_command(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            "Installing with pip"
        )

        if not success:
            print("\n❌ Installation failed")
            sys.exit(1)

    # Verify installation
    print("\n🔍 Verifying installation...")
    try:
        # Try importing palace
        import palace
        print("✅ Palace imports successfully")

        # Check key modules
        from palace.core.hippocampus import Hippocampus
        from palace.api.context import ContextProvider
        from palace.formatters.claude import ClaudeFormatter
        print("✅ All core modules available")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)

    # Test CLI
    print("\n🧪 Testing CLI...")
    cli_test = subprocess.run(
        ["poetry", "run", "palace", "--help"],
        capture_output=True,
        text=True
    )

    if cli_test.returncode == 0:
        print("✅ CLI is working")
        print("\n📋 Available commands:")
        for line in cli_test.stdout.split('\n'):
            if 'Commands:' in line or '  ' + line.strip():
                print(f"   {line.strip()}")
    else:
        print("❌ CLI test failed")
        sys.exit(1)

    # Success message
    print("\n" + "=" * 50)
    print("🎉 Installation complete!")
    print("\n🚀 Next steps:")
    print("   1. Go to your project: cd /path/to/your/project")
    print("   2. Initialize: poetry run palace init")
    print("   3. Ingest code: poetry run palace ingest")
    print("   4. Get context: poetry run palace context src/file.py")
    print("\n📚 Documentation:")
    print("   - QUICKSTART.md: 5-minute guide")
    print("   - CHEATSHEET.md: Quick reference")
    print("   - TUTORIAL.md: Complete tutorial")
    print("   - DEMO.md: Real examples")
    print("\n🌟 Repository: https://github.com/dest92/openpalace")


if __name__ == "__main__":
    main()
