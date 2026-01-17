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


def play_story(tree, start_node_id):
    """
    A simple terminal-based 'Game Engine' to test the flow.
    """
    current_id = start_node_id
    
    while True:
        # 1. Fetch the current node
        node = tree.get_node(current_id)
        
        if not node:
            print(f"Error: Node '{current_id}' not found!")
            break

        # 2. Render the 'Scene'
        print("-" * 40)
        print(f"[{node.speaker}]: \"{node.text}\"")
        print("-" * 40)

        # 3. Check for End of Game
        if not node.choices:
            print("(End of scene)")
            break

        # 4. Display Choices
        print("What do you do?")
        for index, choice in enumerate(node.choices):
            print(f"{index + 1}. {choice['text']}")

        # 5. Get User Input
        while True:
            try:
                user_input = int(input("\nSelect a choice (number): "))
                if 1 <= user_input <= len(node.choices):
                    # Valid choice found! Update the state.
                    choice_data = node.choices[user_input - 1]
                    current_id = choice_data["next_id"]
                    break # Exit input loop, continue game loop
                else:
                    print("Invalid number. Try again.")
            except ValueError:
                print("Please enter a number.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    story = DialogueTree()

    # Create Nodes
    node1 = DialogueNode("start_001", "Mystery Figure", "You've finally arrived. I wasn't sure you'd make it.")
    node2 = DialogueNode("path_aggressive", "Hero", "I don't have time for riddles. Where is the key?")
    node3 = DialogueNode("path_diplomatic", "Hero", "The traffic was terrible. Who are you?")
    
    # Endings
    node4 = DialogueNode("end_fight", "Mystery Figure", "So you choose violence. Pity.")
    node5 = DialogueNode("end_talk", "Mystery Figure", "A polite guest. Rare these days.")

    # Link Choices
    node1.add_choice("Demand answers", "path_aggressive")
    node1.add_choice("Apologize politely", "path_diplomatic")
    
    node2.add_choice("Draw Weapon", "end_fight")
    node3.add_choice("Ask for tea", "end_talk")

    # Add to Tree
    story.add_node(node1)
    story.add_node(node2)
    story.add_node(node3)
    story.add_node(node4)
    story.add_node(node5)

    # RUN THE GAME
    print("--- STARTING DEBUG SESSION ---\n")
    play_story(story, "start_001")