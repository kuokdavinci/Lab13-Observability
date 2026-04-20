import os
import logging
from dotenv import load_dotenv
from langfuse import Langfuse

# Enable debug logging for langfuse
logging.basicConfig(level=logging.DEBUG)
load_dotenv()

def test_raw_client():
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    host = os.getenv('LANGFUSE_HOST')
    
    print(f"Connecting to: {host}")
    print(f"Public Key: {public_key[:10]}...")
    
    langfuse = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
        debug=True
    )
    
    try:
        trace = langfuse.trace(name="DIAGNOSTIC_TEST")
        print(f"Trace created: {trace.id}")
        langfuse.flush()
        print("Flush completed successfully.")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_raw_client()
