import os
import sys
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from google import genai

def main():
    # Load .env without overriding pre-set environment variables
    load_dotenv(override=False)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        print("Error: GEMINI_API_KEY is not set.")
        sys.exit(1)

    # Allow listing accessible models if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--list-models":
        try:
            client = genai.Client(api_key=api_key)
            for model in client.models.list():
                name = model.name
                if name.startswith("models/"):
                    name = name[len("models/"):]
                print(name)
        except Exception as e:
            err_line = str(e).splitlines()[0] if str(e) else "Unknown error"
            if api_key in err_line:
                err_line = err_line.replace(api_key, "[REDACTED]")
            print(f"Error: {e.__class__.__name__}: {err_line}")
            sys.exit(1)
        return

    model_id = os.environ.get("GEMINI_MODEL")
    if not model_id or not model_id.strip():
        print("Error: GEMINI_MODEL is not set in environment or .env.")
        sys.exit(1)

    prompt = "In one concise sentence, what is marine safety?"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
        )
        print(f"Model ID: {model_id}")
        print(f"Response: {response.text.strip()}")
    except Exception as e:
        err_line = str(e).splitlines()[0] if str(e) else "Unknown error"
        if api_key in err_line:
            err_line = err_line.replace(api_key, "[REDACTED]")
        print(f"Error: {e.__class__.__name__}: {err_line}")
        sys.exit(1)

if __name__ == "__main__":
    main()
