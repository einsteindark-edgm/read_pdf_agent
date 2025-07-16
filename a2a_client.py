"""Quick test client for Document Extraction Agent."""
import asyncio
import sys

from app.a2a.client_cli.interaction import DocumentExtractionInteraction


async def main():
    """Main entry point."""
    interaction = DocumentExtractionInteraction()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run automated tests
        await interaction.run_tests()
    else:
        # Run interactive session
        await interaction.interactive_session()


if __name__ == "__main__":
    print("🚀 A2A Document Extraction Client")
    print("Make sure the A2A server is running: python __main__.py")
    print("Run with --test flag for automated tests\n")
    
    asyncio.run(main())