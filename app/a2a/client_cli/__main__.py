"""Main entry point for A2A Client CLI."""
import asyncio
import sys
from .interaction import DocumentExtractionInteraction


async def main():
    """Main entry point for interaction utilities."""
    interaction = DocumentExtractionInteraction()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run automated tests
        await interaction.run_tests()
    else:
        # Run interactive session
        await interaction.interactive_session()


if __name__ == "__main__":
    print("🚀 A2A Document Extraction Client")
    print("Make sure the A2A server is running: python __main__.py\n")
    
    asyncio.run(main())