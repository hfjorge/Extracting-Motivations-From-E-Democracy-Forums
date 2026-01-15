from reddit_scrapper_class import * 
from langchain_community.graphs import Neo4jGraph
import os

graph = Neo4jGraph()

scraper = RedditThreadScraper(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="my_scraping_bot"
)
    
thread_url = "https://www.reddit.com/r/bloodborne/comments/1jlae1s/whats_the_recommended_lv_for_the_dlc/"
if scraper.build_comment_tree(thread_url):
    print(f"\nOP Title: {{scraper.comment_tree[scraper.root_id]['title']}}\n")
    


#upload the base node
# Create nodes
for node_id, node_data in scraper.comment_tree.items():
    if "title" in node_data:  # OP node
        graph.query("""
            CREATE (p:Post {id: $id, title: $title, text: $text, author: $author})
            """, 
            {{"id" : node_data["id"], "title":node_data["title"], "text":node_data["text"], "author":node_data["author"]}}
            )
        
    else:  # Comment node
        graph.query("""
            CREATE (p:Post {id: $id, text: $text, author: $author})
            """, 
            {{"id" : node_data["id"], "text":node_data["text"], "author":node_data["author"]}}
            )

# Create RESPONDS_TO relationships
for node_id, node_data in scraper.comment_tree.items():
    if node_data["parent_id"] and node_data["parent_id"] in scraper.comment_tree:
        graph.query("""
            MATCH (child:Post {id: $child_id}), (parent:Post {id: $parent_id})
            CREATE (child)-[:RESPONDS_TO]->(parent)
        """, 
        {{"child_id":node_id, "parent_id":node_data["parent_id"]}}
        )
