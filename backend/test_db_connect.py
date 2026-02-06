import sys
import time
from src.vector_db import get_vector_db, VectorDBError

print("Testing VectorDB connection and collection creation...")
start = time.time()
try:
    db = get_vector_db()
    print(f"Success! VectorDB initialized in {time.time() - start:.2f} seconds.")
except Exception as e:
    print(f"Failed after {time.time() - start:.2f} seconds.")
    print(f"Error: {e}")
    sys.exit(1)
