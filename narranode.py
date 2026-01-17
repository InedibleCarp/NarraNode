import json

class DialogueNode:
    """
    Represents a single screen of dialogue (a Node).
    """
    def __init__(self, node_id, speaker, text):
        self.node_id = node_id
        self.speaker = speaker
        self.text = text
        self.choices = []

    def add_choice(self, choice_text, next_node_id, effects=None, requirements=None):
        """
        Adds a branching path.
        :param effects: Dict of changes to state (e.g., {'gold': -5})
        :param requirements: Dict of needs to see this option (e.g., {'gold': 5})
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
            "Choices": self.choices
        }

class DialogueTree:
    """
    The Engine: Manages nodes and the Global State (Variables).
    """
    def __init__(self):
        self.nodes = {}
        # Default starting stats
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
            # If stat doesn't exist, assume 0
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

def play_story(tree, start_node_id):
    """
    The Game Loop: Renders nodes and handles input.
    """
    current_id = start_node_id
    
    while True:
        node = tree.get_node(current_id)
        if not node:
            print(f"Error: Node {current_id} not found.")
            break

        # --- DISPLAY UI ---
        print("\n" + "=" * 50)
        print(f"STATS: {tree.state}")
        print("-" * 50)
        print(f"[{node.speaker}]: \"{node.text}\"")
        print("-" * 50)

        if not node.choices:
            print("(End of Story)")
            break

        # --- FILTER & SHOW CHOICES ---
        print("Decisions:")
        available_choices = []
        
        for choice in node.choices:
            # Check if we meet requirements
            is_unlocked = tree.check_requirements(choice['requirements'])
            
            if is_unlocked:
                # Add to list of valid options
                available_choices.append(choice)
                idx = len(available_choices)
                print(f" {idx}. {choice['text']}")
            else:
                # Optional: Show locked choices (greyed out)
                reqs = choice['requirements']
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
                    
                    # Apply effects and Move
                    tree.apply_effects(selected['effects'])
                    current_id = selected['next_id']
                    break
                else:
                    print("Invalid number.")
            except ValueError:
                print("Please enter a number.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    game = DialogueTree()
    
    # Setup specific stats for testing
    game.state['gold'] = 2 # Player starts poor

    # Node 1: The Merchant
    n1 = DialogueNode("shop_01", "Merchant", "That sword costs 10 Gold. Do you have the coin?")
    
    # Node 2: Success
    n2 = DialogueNode("buy_success", "Hero", "Here is the money. (You equip the sword).")
    
    # Node 3: Failure
    n3 = DialogueNode("buy_fail", "Merchant", "Come back when you're not a beggar!")

    # Node 4: Grind for money
    n4 = DialogueNode("work_01", "Narrator", "You scrub floors for a few hours.")


    # --- LINKING ---
    
    # Option 1: Buy sword (REQUIRES 10 GOLD)
    n1.add_choice(
        choice_text="Buy the Sword", 
        next_node_id="buy_success", 
        effects={"gold": -10, "damage": 5},
        requirements={"gold": 10}
    )

    # Option 2: Leave
    n1.add_choice("Leave shop", "buy_fail")

    # Option 3: Work (CORRECTED)
    # This now points to 'work_01' (n4) instead of looping instantly
    n1.add_choice(
        choice_text="Work for coin (+5 Gold)", 
        next_node_id="work_01", 
        effects={"gold": 5}
    )

    # NEW: Add a "Return" link to the Work Node (n4)
    # Otherwise, the game would get stuck on the "You scrub floors" screen!
    n4.add_choice(
        choice_text="Return to shop",
        next_node_id="shop_01"
    )

    game.add_node(n1)
    game.add_node(n2)
    game.add_node(n3)
    game.add_node(n4)

    # Start the engine
    play_story(game, "shop_01")
    
    # Save the result
    game.save_to_json()