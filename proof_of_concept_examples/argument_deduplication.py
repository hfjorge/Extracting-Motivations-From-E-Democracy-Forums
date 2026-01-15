from sentence_transformers import SentenceTransformer, util


# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# New argument (to be checked)
new_argument = "Education is less important than health."

# Existing arguments in the topic (text)
existing_arguments = [
    "Everyone should have access to education without paying.",
    "Health is more important than education.",
    "Free education promotes equal opportunities."
]

print("starting embedding")
# Generate embeddings
new_embedding = model.encode(new_argument, convert_to_tensor=True)
existing_embeddings = model.encode(existing_arguments, convert_to_tensor=True)

print("calculating similarity")
# Calculate similarities
similarities = util.cos_sim(new_embedding, existing_embeddings)

print("checking if it is similar")
# Check if any are very similar (e.g., > 0.90)
threshold = 0.90
duplicate = any(sim > threshold for sim in similarities[0])

# Show results
if duplicate:
    print("Duplicate (or very similar) argument detected!")
else:
    print("Argument is new and can be added.")
