"""Unit tests for the NarraNode dialogue engine (narranode.py)."""

import json
import os
import sys
import tempfile
import pytest

# Add src/ to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import narranode as engine


# ──────────────────────────────────────────────
# DialogueNode
# ──────────────────────────────────────────────

class TestDialogueNode:
    """Tests for the DialogueNode class."""

    def test_basic_construction(self):
        node = engine.DialogueNode("start", "Guard", "Halt! Who goes there?")
        assert node.node_id == "start"
        assert node.speaker == "Guard"
        assert node.text == "Halt! Who goes there?"
        assert node.next_node_id is None
        assert node.choices == []

    def test_construction_with_next_node(self):
        node = engine.DialogueNode("intro", "Narrator", "Welcome.", next_node_id="chapter1")
        assert node.next_node_id == "chapter1"

    def test_add_choice_minimal(self):
        node = engine.DialogueNode("q1", "NPC", "What do you want?")
        node.add_choice("Trade", "trade_node")
        assert len(node.choices) == 1
        assert node.choices[0]["text"] == "Trade"
        assert node.choices[0]["next_id"] == "trade_node"
        assert node.choices[0]["effects"] == {}
        assert node.choices[0]["requirements"] == {}

    def test_add_choice_with_effects(self):
        node = engine.DialogueNode("shop", "Merchant", "Buy a potion?")
        node.add_choice("Buy potion", "bought", effects={"gold": -10, "potions": 1})
        choice = node.choices[0]
        assert choice["effects"] == {"gold": -10, "potions": 1}
        assert choice["requirements"] == {}

    def test_add_choice_with_requirements(self):
        node = engine.DialogueNode("gate", "Guard", "You may pass.")
        node.add_choice("Enter VIP area", "vip", requirements={"reputation": 50})
        choice = node.choices[0]
        assert choice["requirements"] == {"reputation": 50}

    def test_add_choice_with_effects_and_requirements(self):
        node = engine.DialogueNode("shop", "Merchant", "Special item!")
        node.add_choice(
            "Buy rare sword", "bought_sword",
            effects={"gold": -100, "attack": 15},
            requirements={"gold": 100, "level": 5}
        )
        choice = node.choices[0]
        assert choice["effects"] == {"gold": -100, "attack": 15}
        assert choice["requirements"] == {"gold": 100, "level": 5}

    def test_add_multiple_choices(self):
        node = engine.DialogueNode("fork", "Narrator", "A fork in the road.")
        node.add_choice("Go left", "left_path")
        node.add_choice("Go right", "right_path")
        node.add_choice("Turn back", "start")
        assert len(node.choices) == 3
        assert [c["next_id"] for c in node.choices] == ["left_path", "right_path", "start"]

    def test_to_dict(self):
        node = engine.DialogueNode("start", "Guard", "Halt!", next_node_id="next")
        node.add_choice("Fight", "combat", effects={"hp": -5})
        d = node.to_dict()
        assert d == {
            "ID": "start",
            "Speaker": "Guard",
            "Text": "Halt!",
            "NextNode": "next",
            "Choices": [{
                "text": "Fight",
                "next_id": "combat",
                "effects": {"hp": -5},
                "requirements": {}
            }]
        }

    def test_to_dict_no_choices(self):
        node = engine.DialogueNode("end", "Narrator", "The end.")
        d = node.to_dict()
        assert d["Choices"] == []
        assert d["NextNode"] is None


# ──────────────────────────────────────────────
# DialogueTree — Construction & Node Management
# ──────────────────────────────────────────────

class TestDialogueTreeBasics:
    """Tests for DialogueTree construction and node CRUD."""

    def test_default_construction(self):
        tree = engine.DialogueTree()
        assert tree.nodes == {}
        assert tree.initial_state == {}
        assert tree.state == {}

    def test_construction_with_state(self):
        tree = engine.DialogueTree(initial_state={"gold": 100, "hp": 50})
        assert tree.initial_state == {"gold": 100, "hp": 50}
        assert tree.state == {"gold": 100, "hp": 50}

    def test_initial_state_is_copied(self):
        """Modifying state should not affect initial_state."""
        tree = engine.DialogueTree(initial_state={"gold": 100})
        tree.state["gold"] = 0
        assert tree.initial_state["gold"] == 100

    def test_add_and_get_node(self):
        tree = engine.DialogueTree()
        node = engine.DialogueNode("n1", "NPC", "Hello")
        tree.add_node(node)
        assert tree.get_node("n1") is node

    def test_get_nonexistent_node(self):
        tree = engine.DialogueTree()
        assert tree.get_node("missing") is None

    def test_add_node_overwrites(self):
        tree = engine.DialogueTree()
        node1 = engine.DialogueNode("n1", "NPC", "Version 1")
        node2 = engine.DialogueNode("n1", "NPC", "Version 2")
        tree.add_node(node1)
        tree.add_node(node2)
        assert tree.get_node("n1").text == "Version 2"

    def test_multiple_nodes(self):
        tree = engine.DialogueTree()
        for i in range(5):
            tree.add_node(engine.DialogueNode(f"n{i}", "NPC", f"Line {i}"))
        assert len(tree.nodes) == 5
        assert tree.get_node("n3").text == "Line 3"


# ──────────────────────────────────────────────
# DialogueTree — Requirements Checking
# ──────────────────────────────────────────────

class TestCheckRequirements:
    """Tests for DialogueTree.check_requirements()."""

    def setup_method(self):
        self.tree = engine.DialogueTree(initial_state={"gold": 50, "hp": 100, "reputation": 10})

    def test_empty_requirements(self):
        assert self.tree.check_requirements({}) is True

    def test_single_requirement_met(self):
        assert self.tree.check_requirements({"gold": 50}) is True

    def test_single_requirement_exceeded(self):
        assert self.tree.check_requirements({"gold": 10}) is True

    def test_single_requirement_not_met(self):
        assert self.tree.check_requirements({"gold": 51}) is False

    def test_multiple_requirements_all_met(self):
        assert self.tree.check_requirements({"gold": 50, "hp": 100}) is True

    def test_multiple_requirements_one_fails(self):
        assert self.tree.check_requirements({"gold": 50, "hp": 101}) is False

    def test_requirement_for_missing_stat(self):
        """A stat not in state defaults to 0, so any positive requirement fails."""
        assert self.tree.check_requirements({"charisma": 1}) is False

    def test_requirement_zero_for_missing_stat(self):
        """Requiring 0 of a missing stat should pass (0 >= 0)."""
        assert self.tree.check_requirements({"charisma": 0}) is True

    def test_negative_requirement(self):
        """Negative requirement threshold — always met since stats start >= 0."""
        assert self.tree.check_requirements({"gold": -1}) is True


# ──────────────────────────────────────────────
# DialogueTree — Applying Effects
# ──────────────────────────────────────────────

class TestApplyEffects:
    """Tests for DialogueTree.apply_effects()."""

    def setup_method(self):
        self.tree = engine.DialogueTree(initial_state={"gold": 50, "hp": 100})

    def test_empty_effects(self):
        self.tree.apply_effects({})
        assert self.tree.state == {"gold": 50, "hp": 100}

    def test_positive_effect(self):
        self.tree.apply_effects({"gold": 20})
        assert self.tree.state["gold"] == 70

    def test_negative_effect(self):
        self.tree.apply_effects({"gold": -30})
        assert self.tree.state["gold"] == 20

    def test_multiple_effects(self):
        self.tree.apply_effects({"gold": -10, "hp": -25})
        assert self.tree.state["gold"] == 40
        assert self.tree.state["hp"] == 75

    def test_effect_on_new_stat(self):
        """Applying an effect for a stat not in state initializes it to 0 first."""
        self.tree.apply_effects({"mana": 30})
        assert self.tree.state["mana"] == 30

    def test_cumulative_effects(self):
        self.tree.apply_effects({"gold": 10})
        self.tree.apply_effects({"gold": 10})
        self.tree.apply_effects({"gold": -5})
        assert self.tree.state["gold"] == 65

    def test_effect_can_go_negative(self):
        self.tree.apply_effects({"gold": -100})
        assert self.tree.state["gold"] == -50


# ──────────────────────────────────────────────
# DialogueTree — JSON Persistence
# ──────────────────────────────────────────────

class TestJsonPersistence:
    """Tests for save_to_json() and load_from_json()."""

    def _build_sample_tree(self):
        tree = engine.DialogueTree(initial_state={"gold": 100, "hp": 50})
        n1 = engine.DialogueNode("start", "Guard", "Halt!")
        n1.add_choice("Bribe", "bribe_ok", effects={"gold": -20})
        n1.add_choice("Fight", "combat", requirements={"hp": 30})
        tree.add_node(n1)

        n2 = engine.DialogueNode("bribe_ok", "Guard", "Fine, pass.", next_node_id="town")
        tree.add_node(n2)

        n3 = engine.DialogueNode("combat", "Narrator", "You draw your sword.")
        tree.add_node(n3)

        n4 = engine.DialogueNode("town", "Narrator", "Welcome to town.")
        tree.add_node(n4)
        return tree

    def test_save_and_load_round_trip(self, tmp_path):
        filepath = str(tmp_path / "test_story.json")
        original = self._build_sample_tree()
        original.save_to_json(filepath)

        loaded = engine.DialogueTree()
        result = loaded.load_from_json(filepath)

        assert result is True
        assert loaded.initial_state == {"gold": 100, "hp": 50}
        assert loaded.state == {"gold": 100, "hp": 50}
        assert set(loaded.nodes.keys()) == {"start", "bribe_ok", "combat", "town"}

    def test_round_trip_node_data(self, tmp_path):
        filepath = str(tmp_path / "test_story.json")
        original = self._build_sample_tree()
        original.save_to_json(filepath)

        loaded = engine.DialogueTree()
        loaded.load_from_json(filepath)

        node = loaded.get_node("start")
        assert node.speaker == "Guard"
        assert node.text == "Halt!"
        assert len(node.choices) == 2
        assert node.choices[0]["text"] == "Bribe"
        assert node.choices[0]["effects"] == {"gold": -20}
        assert node.choices[1]["requirements"] == {"hp": 30}

    def test_round_trip_linear_flow(self, tmp_path):
        filepath = str(tmp_path / "test_story.json")
        original = self._build_sample_tree()
        original.save_to_json(filepath)

        loaded = engine.DialogueTree()
        loaded.load_from_json(filepath)

        node = loaded.get_node("bribe_ok")
        assert node.next_node_id == "town"

    def test_load_missing_file(self):
        tree = engine.DialogueTree()
        result = tree.load_from_json("/nonexistent/path/story.json")
        assert result is False

    def test_load_old_format(self, tmp_path):
        """Old format: flat dict of nodes, no initial_state wrapper."""
        filepath = str(tmp_path / "old_format.json")
        old_data = {
            "intro": {
                "ID": "intro",
                "Speaker": "Narrator",
                "Text": "Once upon a time...",
                "NextNode": None,
                "Choices": [{"text": "Continue", "next_id": "ch1", "effects": {}, "requirements": {}}]
            }
        }
        with open(filepath, "w") as f:
            json.dump(old_data, f)

        tree = engine.DialogueTree()
        result = tree.load_from_json(filepath)
        assert result is True
        assert tree.initial_state == {}
        assert tree.state == {}
        assert tree.get_node("intro").speaker == "Narrator"
        assert len(tree.get_node("intro").choices) == 1

    def test_save_creates_directories(self, tmp_path):
        filepath = str(tmp_path / "subdir" / "nested" / "story.json")
        tree = engine.DialogueTree()
        tree.add_node(engine.DialogueNode("n1", "NPC", "Hello"))
        # The current implementation doesn't create directories,
        # so this should raise an error
        with pytest.raises(FileNotFoundError):
            tree.save_to_json(filepath)

    def test_save_overwrites_existing(self, tmp_path):
        filepath = str(tmp_path / "story.json")
        tree1 = engine.DialogueTree()
        tree1.add_node(engine.DialogueNode("old", "NPC", "Old data"))
        tree1.save_to_json(filepath)

        tree2 = engine.DialogueTree()
        tree2.add_node(engine.DialogueNode("new", "NPC", "New data"))
        tree2.save_to_json(filepath)

        loaded = engine.DialogueTree()
        loaded.load_from_json(filepath)
        assert loaded.get_node("old") is None
        assert loaded.get_node("new") is not None

    def test_json_file_structure(self, tmp_path):
        """Verify the raw JSON structure on disk."""
        filepath = str(tmp_path / "story.json")
        tree = engine.DialogueTree(initial_state={"gold": 10})
        tree.add_node(engine.DialogueNode("n1", "NPC", "Hi"))
        tree.save_to_json(filepath)

        with open(filepath, "r") as f:
            raw = json.load(f)

        assert "initial_state" in raw
        assert "nodes" in raw
        assert raw["initial_state"] == {"gold": 10}
        assert "n1" in raw["nodes"]


# ──────────────────────────────────────────────
# play_story — Game Loop
# ──────────────────────────────────────────────

class TestPlayStory:
    """Tests for the play_story() game loop function."""

    def _build_linear_story(self):
        tree = engine.DialogueTree()
        n1 = engine.DialogueNode("start", "Narrator", "Begin.", next_node_id="mid")
        n2 = engine.DialogueNode("mid", "Narrator", "Middle.", next_node_id="end")
        n3 = engine.DialogueNode("end", "Narrator", "The End.")
        tree.add_node(n1)
        tree.add_node(n2)
        tree.add_node(n3)
        return tree

    def _build_branching_story(self):
        tree = engine.DialogueTree(initial_state={"gold": 50})
        n1 = engine.DialogueNode("start", "NPC", "Choose.")
        n1.add_choice("Left", "left")
        n1.add_choice("Right", "right")
        tree.add_node(n1)

        n2 = engine.DialogueNode("left", "NPC", "You went left.")
        tree.add_node(n2)

        n3 = engine.DialogueNode("right", "NPC", "You went right.")
        tree.add_node(n3)
        return tree

    def test_missing_start_node(self, capsys):
        tree = engine.DialogueTree()
        engine.play_story(tree, "nonexistent")
        output = capsys.readouterr().out
        assert "not found" in output

    def test_linear_story_reaches_end(self, monkeypatch, capsys):
        tree = self._build_linear_story()
        inputs = iter(["", ""])  # Two Enter presses for linear flow
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        engine.play_story(tree, "start")
        output = capsys.readouterr().out
        assert "Begin." in output
        assert "Middle." in output
        assert "The End." in output
        assert "End of Story" in output

    def test_branching_choice_selection(self, monkeypatch, capsys):
        tree = self._build_branching_story()
        inputs = iter(["1"])  # Select first choice
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        engine.play_story(tree, "start")
        output = capsys.readouterr().out
        assert "Choose." in output
        assert "You went left." in output

    def test_branching_second_choice(self, monkeypatch, capsys):
        tree = self._build_branching_story()
        inputs = iter(["2"])
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        engine.play_story(tree, "start")
        output = capsys.readouterr().out
        assert "You went right." in output

    def test_effects_applied_during_play(self, monkeypatch, capsys):
        tree = engine.DialogueTree(initial_state={"gold": 100})
        n1 = engine.DialogueNode("start", "Merchant", "Buy something?")
        n1.add_choice("Buy sword", "bought", effects={"gold": -50})
        tree.add_node(n1)
        tree.add_node(engine.DialogueNode("bought", "Merchant", "Enjoy!"))

        inputs = iter(["1"])
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        engine.play_story(tree, "start")
        assert tree.state["gold"] == 50

    def test_locked_choice_not_selectable(self, monkeypatch, capsys):
        tree = engine.DialogueTree(initial_state={"gold": 5})
        n1 = engine.DialogueNode("start", "NPC", "Choose.")
        n1.add_choice("Cheap option", "cheap")
        n1.add_choice("Expensive option", "expensive", requirements={"gold": 999})
        tree.add_node(n1)
        tree.add_node(engine.DialogueNode("cheap", "NPC", "Budget choice."))

        inputs = iter(["1"])
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        engine.play_story(tree, "start")
        output = capsys.readouterr().out
        assert "LOCKED" in output
        assert "Budget choice." in output

    def test_all_choices_locked_game_over(self, monkeypatch, capsys):
        tree = engine.DialogueTree(initial_state={"gold": 0})
        n1 = engine.DialogueNode("start", "NPC", "You're stuck.")
        n1.add_choice("VIP door", "vip", requirements={"gold": 1000})
        tree.add_node(n1)

        engine.play_story(tree, "start")
        output = capsys.readouterr().out
        assert "No valid choices" in output or "Game Over" in output


# ──────────────────────────────────────────────
# Visualizer
# ──────────────────────────────────────────────

class TestVisualizer:
    """Tests for the visualizer module."""

    def test_visualize_does_not_crash(self, monkeypatch):
        """Verify visualize_story runs without error (suppress plt.show)."""
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import visualizer

        # Suppress plt.show so no window pops up
        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)

        tree = engine.DialogueTree()
        n1 = engine.DialogueNode("start", "NPC", "Hello")
        n1.add_choice("Go", "end")
        tree.add_node(n1)
        tree.add_node(engine.DialogueNode("end", "NPC", "Bye"))

        # Should not raise
        visualizer.visualize_story(tree)

    def test_visualize_with_linear_and_choice_edges(self, monkeypatch):
        """Verify visualizer handles both edge types."""
        import matplotlib
        matplotlib.use("Agg")
        import visualizer

        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)

        tree = engine.DialogueTree()
        n1 = engine.DialogueNode("a", "NPC", "Line A", next_node_id="b")
        tree.add_node(n1)

        n2 = engine.DialogueNode("b", "NPC", "Line B")
        n2.add_choice("Option 1", "c")
        n2.add_choice("Option 2", "d")
        tree.add_node(n2)

        tree.add_node(engine.DialogueNode("c", "NPC", "Path C"))
        tree.add_node(engine.DialogueNode("d", "NPC", "Path D"))

        visualizer.visualize_story(tree)

    def test_visualize_single_node(self, monkeypatch):
        """A tree with one node and no edges should still render."""
        import matplotlib
        matplotlib.use("Agg")
        import visualizer

        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)

        tree = engine.DialogueTree()
        tree.add_node(engine.DialogueNode("lonely", "NPC", "All alone."))
        visualizer.visualize_story(tree)