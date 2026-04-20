import os
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

def test_connection():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    
    print(f"Checking connection to: {base_url}")
    print(f"Public Key: {public_key[:10]}...")
    
    langfuse = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=base_url
    )
    
    # Try to send a simple trace
    trace = langfuse.trace(name="connection_test")
    trace.generation(name="test_gen", input="test", output="working")
    
    print("Attempting to flush...")
    langfuse.flush()
    print("Flush completed. Check Langfuse UI for 'connection_test' trace.")

if __name__ == "__main__":
    test_connection()
