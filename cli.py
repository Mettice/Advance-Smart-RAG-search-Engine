"""
Command-line interface module.
Provides an interactive terminal chat session and file indexing capability.
"""

import sys
import asyncio
from vector_store import index_file
from rag_pipeline import answer


async def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"Indexing '{path}'...")
        try:
            n = await index_file(path)
            print(f"Successfully loaded and indexed '{path}' ({n} chunks).\n")
        except Exception as e:
            print(f"Error indexing '{path}': {e}")
            return
    else:
        print("Using existing persistent database. (To index a new file: `python cli.py <path_to_file>`)\n")

    print("=" * 60)
    print(" Smart Document Search — Terminal Chat")
    print(" Type 'quit' or 'exit' to terminate the session.")
    print("=" * 60)

    while True:
        try:
            question = input("\n>> ").strip()
            if question.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            if not question:
                continue

            ans, sources = await answer(question)
            print(f"\n{ans}")
            if sources:
                print(f"\n[Sources: {', '.join(sources)}]")

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())
