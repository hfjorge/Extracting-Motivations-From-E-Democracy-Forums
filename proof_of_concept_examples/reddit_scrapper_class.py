import praw
import re

class RedditThreadScraper:
    def __init__(self, client_id, client_secret, user_agent):
        """Initializes the scraper with Reddit API credentials."""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.comment_tree = {}
        self.root_id = None

    def clean_text(self, text):
        """Removes line breaks and extra spaces from the text."""
        return re.sub(r"\s+", " ", text).strip()

    def build_comment_tree(self, thread_url):
        """Builds the comment tree from a Reddit URL."""
        try:
            # Get the thread by URL
            submission = self.reddit.submission(url=thread_url)

            # Clean the OP's title
            op_title = self.clean_text(submission.title)

            # Remove "load more comments"
            submission.comments.replace_more(limit=0)

            # Initialize the comment tree
            self.comment_tree = {}
            self.root_id = submission.id

            # Add the OP as the root
            self.comment_tree[self.root_id] = {
                "id": self.root_id,
                "title": op_title,
                "text": self.clean_text(submission.selftext),
                "author": submission.author.name if submission.author else "Unknown",
                "parent_id": None,
                "children": []
            }

            # Traverse and organize the comments
            for comment in submission.comments.list():
                if comment.author != "AutoModerator":
                    comment_id = comment.id
                    parent_id = comment.parent_id.split("_")[-1]
                    self.comment_tree[comment_id] = {
                        "id": comment_id,
                        "text": self.clean_text(comment.body),
                        "author": comment.author.name if comment.author else "Unknown",
                        "parent_id": parent_id,
                        "children": []
                    }

                    if parent_id in self.comment_tree:
                        self.comment_tree[parent_id]["children"].append(comment_id)

            return True  # Success
        except Exception as e:
            print(f"Error building the comment tree: {e}")
            self.comment_tree = {}
            self.root_id = None
            return False

    def get_comment_tree(self):
        """Returns the comment tree."""
        return self.comment_tree

    def get_root_id(self):
        """Returns the ID of the original post (root of the thread)."""
        return self.root_id

    def print_tree(self, node_id=None, level=0):
        """Prints the comment tree starting from a specific node (default: root)."""
        if not self.comment_tree:
            print("Comment tree is empty.")
            return
        
        if node_id is None:
            node_id = self.root_id
        
        if node_id not in self.comment_tree:
            print(f"Node {node_id} not found in the tree.")
            return
        
        node = self.comment_tree[node_id]
        prefix = "➡" if level == 0 else " " * (level * 4) + "↳"
        print(f"{prefix} {node['author']}: {node['text'][:100]}")
        for child_id in node["children"]:
            self.print_tree(child_id, level + 1)

