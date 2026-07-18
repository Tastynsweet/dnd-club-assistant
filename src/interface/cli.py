from src.engine.engine import process_request

_HELP_TEXT = (
    "I can help you with:\n"
    "  - Register a new character, e.g. \"Register Feilong, a level 4 Monk played by Andy.\"\n"
    "  - List characters, e.g. \"Show me all my characters.\""
)


def format_response(result: dict) -> str:
    status = result.get("status")

    if status == "success":
        lines = [result.get("message", "Success.")]
        data = result.get("data")
        if isinstance(data, list) and data:
            for item in data:
                lines.append(f"  - {item.get('name')} ({item.get('player')})")
        return "\n".join(lines)

    if status == "exists":
        return result.get("message", "That character already exists.")

    if status == "incomplete":
        missing = result.get("missing", [])
        return result.get("message", "Missing information.") + "\n  Missing: " + ", ".join(missing)

    if status == "unknown":
        return result.get("message", "I didn't understand that.") + "\n\n" + _HELP_TEXT

    return result.get("message", "Unexpected response.")


def run_session(process_fn=None):
    if process_fn is None:
        process_fn = process_request

    print("D&D Club Assistant -- type 'quit' or 'exit' to leave.\n")

    while True:
        try:
            user_input = input("You: ")
        except EOFError:
            print("\nGoodbye!")
            return

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            return

        result = process_fn(user_input)
        print("Assistant: " + format_response(result))
        print()


if __name__ == "__main__":
    run_session()