import praw
import re

# API Configuration
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_SECRET",
    user_agent="my_scrapper"
)


# Specific thread URL
thread_url = "https://www.reddit.com/r/audiophile/comments/1jjc1sp/it_finally_happened_a_goodwill_find_of_a_lifetime/"

# Get the thread directly by URL
submission = reddit.submission(url=thread_url)

# Function to clean text (remove line breaks and extra spaces)
def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

# Get the OP title
op_title = clean_text(submission.title)


# Remove "see more comments" to ensure complete structure
submission.comments.replace_more(limit=0)

# Create tree structure for comments
comment_tree = {}

# Add OP (original post) as the root of the tree
comment_tree[submission.id] = {
    "id": submission.id,
    "title": op_title,  # Add the title
    "tags": [submission.link_flair_text] if submission.link_flair_text else [],
    "text": clean_text(submission.selftext),
    "author": submission.author.name if submission.author else "Unknown",
    "parent_id": None,  # The OP has no parent
    "children": []
}

# Iterate through comments and organize them in the tree
for comment in submission.comments.list():
    comment_id = comment.id
    parent_id = comment.parent_id.split("_")[-1]  # Remove "t1_" or "t3_"

    # Add comment to the tree
    comment_tree[comment_id] = {
        "id": comment_id,
        "text": clean_text(comment.body),
        "author": comment.author.name if comment.author else "Unknown",
        "parent_id": parent_id,
        "children": []
    }

    # Associate with the parent (OP or another comment)
    if parent_id in comment_tree:
        comment_tree[parent_id]["children"].append(comment_id)



# Function to print the comment tree
def print_tree(node_id, level=0):
    node = comment_tree[node_id]
    prefix = "➡" if level == 0 else " " * (level * 4) + "↳"
    print(f"{prefix} {node['author']}: {node['text'][:100]}")  # 100 character limit for readability
    for child_id in node["children"]:
        print_tree(child_id, level + 1)


# Display the OP title before the structure
print(f"\nOP Title: {op_title}\n")

# Print structure
print_tree(submission.id)
