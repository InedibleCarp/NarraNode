import json

class DialogueNode:
    """
    Represents a single screen of dialogue.
    """
    def __init__(self, node_id, speaker, text):
        self.node_id = node_id
        self.speaker = speaker
        self.text = text
        # Choices will be a list of dictionaries: 
        # [{'text': 'Say Hello', 'next_id': '2'}]
        self.choices = []

    def add_choice(self, choice_text, next_node_id):
        self.choices.append({
            "text": choice_text,
            "next_id": next_node_id
        })

    def to_dict(self):
        """Converts the object to a dictionary for JSON export."""
        return {
            "ID": self.node_id,
            "Speaker": self.speaker,
            "Text": self.text,
            "Choices": self.choices
        }

class DialogueTree:
    """
    Manages the collection of nodes.
    """
    def __init__(self):
        self.nodes = {} # Storing nodes by ID for easy lookup

    def add_node(self, node):
        if node.node_id in self.nodes:
            print(f"Warning: Overwriting node {node.node_id}")
        self.nodes[node.node_id] = node

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def save_to_json(self, filename="story_data.json"):
        # Convert all nodes to dicts
        data = {id: node.to_dict() for id, node in self.nodes.items()}
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Successfully saved {len(self.nodes)} nodes to {filename}")

# --- AI CO-WRITER STUB ---
# Since you have AI training experience, this is where you'd hook in an API.
def generate_ai_suggestion(prompt_context):
    # TODO: Connect to OpenAI/Ollama API here
    # return api_response
    pass

# --- MAIN EXECUTION (Testing the logic) ---
if __name__ == "__main__":
    # 1. Create the Manager
    story = DialogueTree()

    # 2. Create Nodes (The "Scenes")
    # Node 1: The Intro
    node1 = DialogueNode(
        node_id="start_001", 
        speaker="Mystery Figure", 
        text="You've finally arrived. I wasn't sure you'd make it."
    )
    
    # Node 2: Aggressive path
    node2 = DialogueNode(
        node_id="path_aggressive", 
        speaker="Hero", 
        text="I don't have time for riddles. Where is the key?"
    )

    # Node 3: Diplomatic path
    node3 = DialogueNode(
        node_id="path_diplomatic", 
        speaker="Hero", 
        text="The traffic was terrible. Who are you?"
    )

    # 3. Link them via Choices
    node1.add_choice("Demand answers", "path_aggressive")
    node1.add_choice("Apologize politely", "path_diplomatic")

    # 4. Add to the Story Manager
    story.add_node(node1)
    story.add_node(node2)
    story.add_node(node3)

    # 5. Export to JSON
    story.save_to_json("my_visual_novel.json")