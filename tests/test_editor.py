"""Unit tests for the NarraNode editor status bar (editor.py)."""

import os
import sys
import pytest

# Add src/ to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Tkinter requires a display; skip all tests in this module if unavailable
tk = pytest.importorskip("tkinter")


@pytest.fixture
def app():
    """Create a NodeEditorApp instance for testing, then clean up."""
    root = tk.Tk()
    root.withdraw()  # Hide the window during tests
    import editor
    application = editor.NodeEditorApp(root)
    yield application
    root.destroy()


class TestStatusBar:
    """Tests for the status bar widget and show_status method."""

    def test_status_bar_exists(self, app):
        assert hasattr(app, 'status_bar')
        assert app.status_bar.cget("text") == "Ready"

    def test_show_status_success(self, app):
        app.show_status("Node saved.", "success")
        assert app.status_bar.cget("text") == "Node saved."
        assert app.status_bar.cget("fg") == "#2e7d32"

    def test_show_status_warning(self, app):
        app.show_status("Please select a node.", "warning")
        assert app.status_bar.cget("text") == "Please select a node."
        assert app.status_bar.cget("fg") == "#e65100"

    def test_show_status_error(self, app):
        app.show_status("Something broke.", "error")
        assert app.status_bar.cget("text") == "Something broke."
        assert app.status_bar.cget("fg") == "#c62828"

    def test_show_status_info(self, app):
        app.show_status("Just a note.", "info")
        assert app.status_bar.cget("text") == "Just a note."
        assert app.status_bar.cget("fg") == "#555555"

    def test_show_status_default_level(self, app):
        app.show_status("Default level message.")
        assert app.status_bar.cget("text") == "Default level message."
        assert app.status_bar.cget("fg") == "#555555"

    def test_show_status_overwrites_previous(self, app):
        app.show_status("First message.", "success")
        app.show_status("Second message.", "warning")
        assert app.status_bar.cget("text") == "Second message."
        assert app.status_bar.cget("fg") == "#e65100"

    def test_timer_is_set(self, app):
        assert app._status_timer is None
        app.show_status("Test.", "info")
        assert app._status_timer is not None

    def test_timer_is_replaced_on_new_message(self, app):
        app.show_status("First.", "info")
        first_timer = app._status_timer
        app.show_status("Second.", "info")
        second_timer = app._status_timer
        # The timer ID should change (old one cancelled, new one created)
        assert first_timer != second_timer


class TestEditorStatusIntegration:
    """Tests that editor actions use the status bar instead of popups."""

    def test_save_node_shows_status(self, app):
        app.entry_id.insert(0, "test_node")
        app.entry_speaker.insert(0, "NPC")
        app.text_content.insert("1.0", "Hello there.")
        app.save_node()
        assert "test_node" in app.status_bar.cget("text")
        assert "saved" in app.status_bar.cget("text").lower()
        assert app.status_bar.cget("fg") == "#2e7d32"  # success green

    def test_save_empty_id_shows_error_popup(self, app):
        """Empty Node ID should still use a messagebox (showerror), not status bar."""
        # We can't easily test messagebox without mocking, but we can verify
        # the status bar was NOT updated (it stays "Ready")
        # The messagebox.showerror will be called but since we don't interact,
        # we just verify no crash occurs by mocking it
        from unittest.mock import patch
        with patch("editor.messagebox.showerror") as mock_err:
            app.save_node()
            mock_err.assert_called_once()
        # Status bar should still be at default since showerror was used
        assert app.status_bar.cget("text") == "Ready"

    def test_delete_no_selection_shows_warning(self, app):
        app.current_node_id = None
        app.delete_node()
        assert "select a node" in app.status_bar.cget("text").lower()
        assert app.status_bar.cget("fg") == "#e65100"  # warning orange

    def test_open_choice_no_selection_shows_warning(self, app):
        app.current_node_id = None
        app.open_choice_window()
        assert "save or select" in app.status_bar.cget("text").lower()
        assert app.status_bar.cget("fg") == "#e65100"

    def test_show_graph_empty_shows_warning(self, app):
        app.show_graph()
        assert "no nodes" in app.status_bar.cget("text").lower()
        assert app.status_bar.cget("fg") == "#e65100"

    def test_export_json_shows_status(self, app, tmp_path, monkeypatch):
        # Monkeypatch save_to_json to avoid filesystem side effects
        monkeypatch.setattr(app.tree, "save_to_json", lambda *a, **kw: None)
        app.export_json()
        assert "exported" in app.status_bar.cget("text").lower()
        assert app.status_bar.cget("fg") == "#2e7d32"

    def test_delete_node_shows_success(self, app):
        """After confirming deletion, status bar should show success."""
        import narranode as engine
        from unittest.mock import patch

        app.tree.add_node(engine.DialogueNode("del_me", "NPC", "Bye"))
        app.current_node_id = "del_me"
        app.refresh_list()

        with patch("editor.messagebox.askyesno", return_value=True):
            app.delete_node()
        assert "del_me" in app.status_bar.cget("text")
        assert "deleted" in app.status_bar.cget("text").lower()
        assert app.status_bar.cget("fg") == "#2e7d32"

    def test_save_node_warns_when_next_node_set_and_choices_exist(self, app):
        """Saving a node with next_node_id while it already has choices should show a warning."""
        import narranode as engine

        # Create a node with a choice already added
        node = engine.DialogueNode("dual_node", "NPC", "I have both.")
        node.add_choice("Option A", "node_a")
        app.tree.add_node(node)
        app.current_node_id = "dual_node"
        app.refresh_list()

        # Fill in the form with a next_node value
        app.entry_id.insert(0, "dual_node")
        app.entry_speaker.insert(0, "NPC")
        app.text_content.insert("1.0", "I have both.")
        app.entry_next_node.insert(0, "some_next_node")

        app.save_node()

        assert app.status_bar.cget("fg") == "#e65100"  # warning orange
        status = app.status_bar.cget("text").lower()
        assert "warning" in status
        assert "next node" in status or "ignored" in status

    def test_save_node_success_when_next_node_set_and_no_choices(self, app):
        """Saving a node with only next_node_id (no choices) should show success, not a warning."""
        app.entry_id.insert(0, "linear_node")
        app.entry_speaker.insert(0, "Narrator")
        app.text_content.insert("1.0", "Moving on.")
        app.entry_next_node.insert(0, "next_node")

        app.save_node()

        assert app.status_bar.cget("fg") == "#2e7d32"  # success green
        assert "saved" in app.status_bar.cget("text").lower()

    def test_add_choice_warns_when_next_node_already_set(self, app):
        """Adding a choice to a node that has next_node_id should show a warning."""
        import narranode as engine

        # Create a node with next_node_id already set
        node = engine.DialogueNode("next_node_conflict", "NPC", "I have a next node.", next_node_id="some_target")
        app.tree.add_node(node)
        app.current_node_id = "next_node_conflict"
        app.refresh_list()

        # Open choice window
        app.open_choice_window()

        # Find the Toplevel window
        win = None
        for child in app.root.winfo_children():
            if isinstance(child, tk.Toplevel):
                win = child
                break
        assert win is not None

        # Collect all ttk.Entry widgets in depth-first order (c_text, c_next, c_effects, c_reqs)
        def collect_entries(widget):
            result = []
            for child in widget.winfo_children():
                if isinstance(child, tk.ttk.Entry):
                    result.append(child)
                result.extend(collect_entries(child))
            return result

        entries = collect_entries(win)
        assert len(entries) >= 2
        entries[0].insert(0, "Test Choice")  # c_text
        entries[1].insert(0, "target_node")  # c_next

        # Find and invoke the "Add Choice" button
        def find_button(widget, text):
            for child in widget.winfo_children():
                if isinstance(child, tk.ttk.Button) and child.cget("text") == text:
                    return child
                found = find_button(child, text)
                if found:
                    return found
            return None

        add_btn = find_button(win, "Add Choice")
        assert add_btn is not None
        add_btn.invoke()

        # Should show a warning about next_node_id conflict
        assert app.status_bar.cget("fg") == "#e65100"  # warning orange
        status = app.status_bar.cget("text").lower()
        assert "warning" in status
        assert "next node" in status or "ignored" in status

        win.destroy()