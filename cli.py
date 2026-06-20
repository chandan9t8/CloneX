import sys
from brain.query import ask
from agents.agent import run_web_only
from dotenv import load_dotenv


def main():
    load_dotenv()

    from langfuse import get_client
    langfuse = get_client()
    if langfuse.auth_check():
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")

    # validating the input
    if len(sys.argv) < 3 or sys.argv[1] != "ask":
        print('Usage: python cli.py ask "<question>"', file=sys.stderr)
        sys.exit(1)

    question = " ".join(sys.argv[2:])
    result = ask(question)

    if not result["sources"]:
        print("\nNo relevant notes found in vault. Searching the web...\n")
        answer = run_web_only(question)
        print(f"{answer}\n")
    else:
        print(f"\n{result['answer']}\n")
        print("Sources:")
        for s in result["sources"]:
            heading = f" › {s['heading']}" if s["heading"] else ""
            print(f"  [{s['score']:.3f}] {s['folder']}/{s['title']}{heading}")

if __name__ == "__main__":
    main()
