from dotenv import load_dotenv
import os
import time
from app.tracing import observe, langfuse_context

load_dotenv()

@observe()
def test_trace():
    print(f"Testing Langfuse with Public Key: {os.getenv('LANGFUSE_PUBLIC_KEY')[:10]}...")
    langfuse_context.update_current_trace(name="Manual Test Trace")
    time.sleep(1)
    print("Sending...")

if __name__ == "__main__":
    test_trace()
    # Force flush
    from langfuse import Langfuse
    Langfuse().flush()
    print("Done. Check your Langfuse dashboard now.")
