import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_neo4j import Neo4jGraph

# Load environment variables
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Connect to Neo4j
#driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
graph = Neo4jGraph()

# Instantiate local LLM with Ollama
llm = ChatOllama(model="llama3.1")


# Function to fetch parent posts (up to 3 levels)
def get_parent_posts(post_id: str, max_levels: int = 3):
    query = f"""
    MATCH (child:Post {{id: $post_id}})-[:RESPONDS_TO*1..{max_levels}]->(parent:Post)
    WHERE toLower(parent.text) <> '[removed]'
    RETURN parent.text AS text, parent.id AS id
    ORDER BY size(parent.text) DESC
    """
    results = graph.query(query, params={{"post_id": post_id}})
    return [{{"id": row["id"], "text": row["text"]}} for row in results]


# Function to fetch the text of the current post
def get_post_text(post_id: str):
    query = """
    MATCH (p:Post {id: $post_id})
    RETURN p.text AS text
    """
    result = graph.query(query, params={{"post_id": post_id}})
    return result[0]["text"] if result else None

# Function to summarize text with LLM
def summarize_text(text: str) -> str:
    prompt = f"""
    Summarize the following post in a concise and informative way. Only keep what is essential to understand the point made:

    """{text}"""
    """
    return llm.invoke(prompt).content

# Main function to build prompt with summarized context
def generate_prompt_with_context(post_id: str, max_parents: int = 3):
    parents = get_parent_posts(post_id, max_levels=max_parents)
    child_post = get_post_text(post_id)

    if not child_post:
        raise ValueError("Child post not found.")

    summarized_context = []
    for p in parents[:max_parents]:
        summary = summarize_text(p["text"])
        summarized_context.append(f"- {summary}")
        

    final_context = "\n".join(summarized_context)

    prompt = f"""
You are analyzing a comment in a political discussion thread.

Context from previous posts (summarized):
{final_context}

Current comment to analyze:
"""{child_post}"""

Your task:
- Extract the main argument.
- Identify the motivation behind the argument.
- Categorize the motivation using Max-Neef's framework.
"""
    return prompt


# Example of use
if __name__ == "__main__":
    post_id_input = "mlk6gmm"  # Replace with a real ID from your database
    generated_prompt = generate_prompt_with_context(post_id_input)
    print(generated_prompt)
