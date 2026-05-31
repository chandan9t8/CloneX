import os
import sys

from dotenv import load_dotenv


def main():
    load_dotenv()

    if len(sys.argv) < 3 or sys.argv[1] != "ask":
        print("Usage: python cli.py ask \"<question>\"", file=sys.stderr)
        sys.exit(1)

    question = " ".join(sys.argv[2:])

    from brain.query import ask
    result = ask(question)

    print(f"\n{result['answer']}\n")

    if result["sources"]:
        print("Sources:")
        for s in result["sources"]:
            heading = f" › {s['heading']}" if s["heading"] else ""
            print(f"  [{s['score']:.3f}] {s['folder']}/{s['title']}{heading}")


if __name__ == "__main__":
    main()
