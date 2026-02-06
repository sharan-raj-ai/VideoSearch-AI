from src.vector_db import get_vector_db, COLLECTION_NAME
from qdrant_client.http import models

db = get_vector_db()
client = db.client

print(f"Creating indices for {COLLECTION_NAME}...")

# Video ID index
client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="video_id",
    field_schema=models.PayloadSchemaType.KEYWORD
)
print("Created video_id index")

# Type index
client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="type",
    field_schema=models.PayloadSchemaType.KEYWORD
)
print("Created type index")
print("Done!")
