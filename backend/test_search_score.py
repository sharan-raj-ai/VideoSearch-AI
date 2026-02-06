from src.vector_db import get_vector_db, COLLECTION_NAME
from src.ai_service import get_ai_service
from qdrant_client.http import models

db = get_vector_db()
ai = get_ai_service()
client = db.client

query = "middle finger"
video_id = "72ec1f8f-dc2e-41db-9f3b-eecb5e340f37"

print(f"Embedding query: '{query}'...")
query_vec = ai.get_query_embedding(query)

print(f"Searching for video {video_id} with threshold 0.0...")
results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=query_vec,
    query_filter=models.Filter(
        must=[models.FieldCondition(key="video_id", match=models.MatchValue(value=video_id))]
    ),
    limit=5,
    with_payload=True,
    score_threshold=0.0
)

print(f"Found {len(results.points)} results:")
for hit in results.points:
    print(f" - Time: {hit.payload.get('timestamp')}s | Score: {hit.score:.4f} | Type: {hit.payload.get('type')}")
    if hit.payload.get('text'):
        print(f"   Text: {hit.payload.get('text')}")
