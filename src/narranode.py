import json
import os

class DialogueNode:
    """
    Represents a single screen of dialogue (a Node).
    """
    def __init__(self, node_id, speaker, text, next_node_id=None):
        self.node_id = node_id
        self.speaker = speaker
        self.text = text
        self.next_node_id = next_node_id  # For linear flow (no choices)
        self.choices = []

    def add_choice(self, choice_text, next_node_id, effects=None, requirements=None):
        """
        Adds a branching path with optional logic.
        """
        self.choices.append({
            "text": choice_text,
            "next_id": next_node_id,
            "effects": effects or {},
            "requirements": requirements or {} 
        })

    def to_dict(self):
        """Converts object to dictionary for JSON export."""
        return {
            "ID": self.node_id,
            "Speaker": self.speaker,
            "Text": self.text,
            "NextNode": self.next_node_id,  # Linear flow target
            "Choices": self.choices
        }

class DialogueTree:
    """
    The Engine: Manages nodes and the Global State (Variables).
    """
    def __init__(self):
        self.nodes = {}
        # Global State (Variables like Health, Gold, Flags)
        self.state = {
            "gold": 0,
            "honor": 0,
            "hp": 100
        }

    def add_node(self, node):
        self.nodes[node.node_id] = node

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def check_requirements(self, requirements):
        """
        Returns True if player meets ALL requirements.
        Example: reqs={'gold': 5} -> Checks if state['gold'] >= 5
        """
        for stat, value in requirements.items():
            current_val = self.state.get(stat, 0)
            if current_val < value:
                return False
        return True

    def apply_effects(self, effects):
        """Updates the global state based on the choice taken."""
        for stat, value in effects.items():
            if stat not in self.state:
                self.state[stat] = 0
            
            self.state[stat] += value
            print(f"   >>> [Effect] {stat} changed by {value} (Now: {self.state[stat]})")

    def save_to_json(self, filename="story_data.json"):
        data = {id: node.to_dict() for id, node in self.nodes.items()}
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        print(f"\n[System] Saved {len(self.nodes)} nodes to {filename}")

    def load_from_json(self, filename="story_data.json"):
        """Loads nodes from a JSON file into memory."""
        if not os.path.exists(filename):
            print(f"[System] File '{filename}' not found.")
            return False

        with open(filename, "r") as f:
            data = json.load(f)

        self.nodes = {}
        for node_id, node_data in data.items():
            # Reconstruct the Node object
            new_node = DialogueNode(
                node_data["ID"],
                node_data["Speaker"],
                node_data["Text"],
                next_node_id=node_data.get("NextNode")  # Load linear flow target
            )

            # Reconstruct Choices
            for choice in node_data["Choices"]:
                new_node.add_choice(
                    choice["text"],
                    choice["next_id"],
                    effects=choice.get("effects"),
                    requirements=choice.get("requirements")
                )

            self.add_node(new_node)
        
        print(f"[System] Loaded {len(self.nodes)} nodes from {filename}")
        return True

def play_story(tree, start_node_id):
    """
    The Game Loop: Renders nodes and handles input.
    """
    current_id = start_node_id
    
    while True:
        node = tree.get_node(current_id)
        if not node:
            print(f"Error: Node '{current_id}' not found.")
            break

        # --- DISPLAY UI ---
        print("\n" + "=" * 50)
        print(f"STATS: {tree.state}")
        print("-" * 50)
        print(f"[{node.speaker}]: \"{node.text}\"")
        print("-" * 50)

        # --- LINEAR FLOW (No choices, auto-advance) ---
        if not node.choices:
            if node.next_node_id:
                input("\n[Press Enter to continue...]")
                current_id = node.next_node_id
                continue
            else:
                print("(End of Story)")
                break

        # --- FILTER & SHOW CHOICES ---
        print("Decisions:")
        available_choices = []
        
        for choice in node.choices:
            is_unlocked = tree.check_requirements(choice.get('requirements', {}))
            
            if is_unlocked:
                available_choices.append(choice)
                idx = len(available_choices)
                print(f" {idx}. {choice['text']}")
            else:
                # Show locked choices
                reqs = choice.get('requirements', {})
                print(f" [LOCKED] {choice['text']} (Requires: {reqs})")

        if not available_choices:
            print("No valid choices available! (Game Over)")
            break

        # --- GET INPUT ---
        while True:
            try:
                sel = int(input("\nSelection #: "))
                if 1 <= sel <= len(available_choices):
                    selected = available_choices[sel - 1]
                    tree.apply_effects(selected.get('effects', {}))
                    current_id = selected['next_id']
                    break
                else:
                    print("Invalid number.")
            except ValueError:
                print("Please enter a number.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    game = DialogueTree()
    
    print("--- NarraNode CLI Engine ---")
    
    # Try to load existing data
    if game.load_from_json("story_data.json"):
        # Auto-detect the first node ID to start with
        first_node_id = list(game.nodes.keys())[0]
        
        # Optional: Ask user for starting node
        # first_node_id = input(f"Enter starting Node ID (Default: {first_node_id}): ") or first_node_id
        
        play_story(game, first_node_id)
    else:
        print("\nNo story file found!")
        print("Run 'editor.py' first to create your story, then run this script to play it.")