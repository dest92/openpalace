#!/usr/bin/env python3
"""
Palace Mental MCP Server - Demo Usage

Demonstrates how to use the Palace Mental MCP server
from a Python client.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def demo_query_artifact():
    """Demo: Query an artifact and get TOON context."""
    print("=" * 60)
    print("Demo 1: Query Artifact")
    print("=" * 60)

    # Connect to MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"\n✅ Available tools: {len(tools.tools)}")
            for tool in tools.tools[:5]:  # Show first 5
                print(f"  - {tool.name}: {tool.description[:60]}...")

            # Call query_artifact tool
            print("\n🔍 Querying artifact...")
            result = await session.call_tool(
                "query_artifact",
                arguments={
                    "artifact_id": "src/auth/authenticate.py",
                    "include_dependencies": True,
                    "max_depth": 2
                }
            )

            print(f"\n📄 Result:")
            print(result.content[0].text if result.content else "No content")


async def demo_compression():
    """Demo: Compress code to TOON format."""
    print("\n" + "=" * 60)
    print("Demo 2: Code Compression")
    print("=" * 60)

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Compress Python code
            code = """
def authenticate(username, password):
    user = validate_user(username)
    if user and check_password(password, user.password_hash):
        return create_token(user)
    return None
""".strip()

            print(f"\n📝 Original code ({len(code)} chars):")
            print(code)

            result = await session.call_tool(
                "compress_code",
                arguments={
                    "code": code,
                    "language": "python",
                    "compact": True
                }
            )

            print(f"\n🗜️  Compressed to TOON format:")
            print(result.content[0].text if result.content else "No content")


async def demo_resources():
    """Demo: Read Palace Mental statistics."""
    print("\n" + "=" * 60)
    print("Demo 3: Read Statistics Resource")
    print("=" * 60)

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available resources
            resources = await session.list_resources()
            print(f"\n✅ Available resources: {len(resources.resources)}")
            for resource in resources.resources[:5]:
                print(f"  - {resource.uri}")

            # Read statistics
            print("\n📊 Reading statistics...")
            result = await session.read_resource("stats://overview")

            print(f"\n📈 Statistics:")
            print(result.contents[0].text if result.contents else "No data")


async def demo_prompts():
    """Demo: Use prompt templates."""
    print("\n" + "=" * 60)
    print("Demo 4: Use Prompt Template")
    print("=" * 60)

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available prompts
            prompts = await session.list_prompts()
            print(f"\n✅ Available prompts: {len(prompts.prompts)}")
            for prompt in prompts.prompts[:5]:
                print(f"  - {prompt.name}: {prompt.description[:60]}...")

            # Get prompt template
            print("\n📋 Getting 'explain_code' prompt template...")
            result = await session.get_prompt(
                "explain_code",
                arguments={
                    "artifact_id": "src/auth/authenticate.py",
                    "audience": "developer",
                    "detail_level": "standard"
                }
            )

            print(f"\n📝 Prompt template:")
            print(result.messages[0].content.text if result.messages else "No content")


async def main():
    """Run all demos."""
    print("""
╔══════════════════════════════════════════════════════════╗
║  Palace Mental MCP Server - Demo                          ║
║  Model Context Protocol Integration                       ║
╚══════════════════════════════════════════════════════════╝
    """)

    try:
        # Demo 1: Query artifact
        await demo_query_artifact()

        # Demo 2: Code compression
        await demo_compression()

        # Demo 3: Read resources
        await demo_resources()

        # Demo 4: Use prompts
        await demo_prompts()

        print("\n" + "=" * 60)
        print("✅ All demos completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
