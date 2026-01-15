from neo4j import GraphDatabase
import requests
import numpy as np
import os

# --- SETTINGS ---
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "mxbai-embed-large"

# --- NEO4J CONNECTION ---
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# --- 1. Generate embedding with mxbai via Ollama ---
def generate_embedding(text):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": text
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json()["embedding"]


# --- 2. Insert post into the graph with embedding ---
def insert_post(tx, text, topic, embedding):
    tx.run("""
        CREATE (p:Post {
            id: randomUUID(),
            text: $text,
            topic_title: $topic,
            embedding: $embedding
        })
    """, text=text, topic=topic, embedding=embedding)


# --- 3. Create vector index (only once) ---
def create_vector_index(tx):
    tx.run("""
        CREATE VECTOR INDEX postEmbeddingIndex IF NOT EXISTS
        FOR (p:Post) ON (p.embedding)
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 1024,
                `vector.similarity_function`: 'cosine'
            }
        }
    """)


# --- 4. Perform vector query and retrieve context ---
def retrieve_context(tx, embedding, k=3):
    result = tx.run("""
        CALL db.index.vector.queryNodes('postEmbeddingIndex', $k, $embedding)
        YIELD node, score
        RETURN node.text AS text, score
    """, embedding=embedding, k=k)
    return [(r['text'], r['score']) for r in result]


# --- DEMO EXECUTION ---
new_text = """Angle Matters: Most kitchen knives are sharpened at a 15-20° angle per side, while Japanese knives often use a sharper 10-15° angle for precision cutting.
Whetstone Grit: Whetstones come in different grits—coarse (200-800) for reshaping, medium (1000-3000) for sharpening, and fine (4000-8000) for polishing.
Honing vs. Sharpening: Honing with a steel rod realigns a blade’s edge but doesn’t remove metal; sharpening actually grinds away material to create a new edge.
Burr Formation: A good sharpening session creates a burr—a thin, raised edge of metal—indicating the blade is ready for finer honing or polishing.
Stropping: Stropping on leather (often with a compound) polishes the edge to a razor-like finish, removing microscopic imperfections.
Ceramic Knives: Ceramic blades require diamond stones for sharpening due to their hardness, unlike steel knives, which work with standard stones.
Frequency: Home cooks typically need to sharpen knives every 6-12 months, depending on use, but professional chefs may sharpen weekly.
Pull-Through Sharpeners: These devices are convenient but often remove too much metal, reducing a knife’s lifespan compared to stones or professional sharpening.
Edge Types: Knives can have single-bevel (e.g., traditional Japanese sushi knives) or double-bevel edges, affecting sharpening technique.
Test Sharpness: A sharp knife should effortlessly slice through paper or shave hair without catching, a common way to check the edge’s quality."""
topic = "knife sharpening"

with driver.session() as session:
    new_embedding = generate_embedding(new_text)

    # 1. Create vector index (if it doesn't exist yet)
    session.execute_write(create_vector_index)

    # 2. Insert new post
    session.execute_write(insert_post, new_text, topic, new_embedding)

    # 3. Retrieve relevant context
    context = session.execute_read(retrieve_context, new_embedding)

    print("\n--- Relevant Context ---")
    for text, score in context:
        print(f"{{score:.3f}}: {{text}}")
