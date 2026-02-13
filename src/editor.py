import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel
import json
import narranode as engine
import visualizer as visualizer

class NodeEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NarraNode Editor")
        self.root.geometry("800x500")

        self.tree = engine.DialogueTree()
        self.current_node_id = None # Track what we are editing
        self._status_timer = None  # Track auto-clear timer

        # --- STATUS BAR (pack first so it anchors to bottom) ---
        self.status_bar = tk.Label(root, text="Ready", anchor="w",
                                   bg="#f0f0f0", fg="#555555",
                                   relief="sunken", padx=10, pady=4)
        self.status_bar.pack(side="bottom", fill="x")

        # --- LEFT PANEL (List) ---
        self.left_frame = tk.Frame(root, width=250, bg="#e0e0e0")
        self.left_frame.pack(side="left", fill="y")
        
        tk.Label(self.left_frame, text="Nodes List", bg="#e0e0e0").pack(pady=5)
        
        # Add Scrollbar to list
        self.list_scroll = tk.Scrollbar(self.left_frame)
        self.list_scroll.pack(side="right", fill="y")
        
        self.node_listbox = tk.Listbox(self.left_frame, yscrollcommand=self.list_scroll.set)
        self.node_listbox.pack(fill="both", expand=True, padx=5)
        self.list_scroll.config(command=self.node_listbox.yview)
        
        self.node_listbox.bind('<<ListboxSelect>>', self.load_selected_node)
        
        # --- RIGHT PANEL (Editor) ---
        self.right_frame = tk.Frame(root, padx=20, pady=20)
        self.right_frame.pack(side="right", fill="both", expand=True)

        # ID Field
        tk.Label(self.right_frame, text="Node ID (Unique):").pack(anchor="w")
        self.entry_id = tk.Entry(self.right_frame)
        self.entry_id.pack(fill="x", pady=(0, 10))

        # Speaker Field
        tk.Label(self.right_frame, text="Speaker Name:").pack(anchor="w")
        self.entry_speaker = tk.Entry(self.right_frame)
        self.entry_speaker.pack(fill="x", pady=(0, 10))

        # Text Field
        tk.Label(self.right_frame, text="Dialogue Text:").pack(anchor="w")
        self.text_content = tk.Text(self.right_frame, height=5)
        self.text_content.pack(fill="x", pady=(0, 10))

        # Linear Flow Field (Next Node)
        tk.Label(self.right_frame, text="Next Node (Linear Flow - leave empty for choices):").pack(anchor="w")
        self.entry_next_node = tk.Entry(self.right_frame)
        self.entry_next_node.pack(fill="x", pady=(0, 10))

        # Buttons Row
        self.btn_frame = tk.Frame(self.right_frame)
        self.btn_frame.pack(fill="x", pady=10)
        
        tk.Button(self.btn_frame, text="Save Node", command=self.save_node, bg="#dddddd").pack(side="left", padx=5)
        tk.Button(self.btn_frame, text="Clear", command=self.clear_fields, bg="#f0f0f0").pack(side="left", padx=5)
        tk.Button(self.btn_frame, text="Delete", command=self.delete_node, bg="#ffb3ba").pack(side="left", padx=5)
        tk.Button(self.btn_frame, text="Manage Choices", command=self.open_choice_window, bg="#add8e6").pack(side="left", padx=5)

        # --- NEW BUTTONS ---
        tk.Button(self.btn_frame, text="Show Map", command=self.show_graph, bg="#ffcccb").pack(side="left", padx=5)
        tk.Button(self.btn_frame, text="Global Variables", command=self.open_variables_window, bg="#c5e1a5").pack(side="left", padx=5)

        tk.Button(self.btn_frame, text="Export JSON", command=self.export_json).pack(side="right")

    def show_status(self, message, level="info"):
        """Display a message in the status bar that auto-clears after a few seconds.

        Levels: 'success' (green), 'warning' (orange), 'error' (red), 'info' (gray).
        """
        colors = {
            "success": "#2e7d32",
            "warning": "#e65100",
            "error":   "#c62828",
            "info":    "#555555",
        }
        durations = {
            "success": 3000,
            "warning": 4000,
            "error":   5000,
            "info":    3000,
        }
        self.status_bar.config(text=message, fg=colors.get(level, "#555555"))

        # Cancel any previous auto-clear timer
        if self._status_timer is not None:
            self.root.after_cancel(self._status_timer)

        self._status_timer = self.root.after(
            durations.get(level, 3000),
            lambda: self.status_bar.config(text="Ready", fg="#555555")
        )

    def save_node(self):
        """Saves current fields to the node object."""
        node_id = self.entry_id.get().strip()
        speaker = self.entry_speaker.get().strip()
        text = self.text_content.get("1.0", tk.END).strip()
        next_node = self.entry_next_node.get().strip() or None  # Linear flow target

        if not node_id:
            messagebox.showerror("Error", "Node ID is required!")
            return

        # Check if node exists to preserve choices
        existing_node = self.tree.get_node(node_id)

        if existing_node:
            # Update existing
            existing_node.speaker = speaker
            existing_node.text = text
            existing_node.next_node_id = next_node  # Update linear flow
            # We DO NOT overwrite choices here, so they stay safe
        else:
            # Create new
            new_node = engine.DialogueNode(node_id, speaker, text, next_node_id=next_node)
            self.tree.add_node(new_node)

        self.current_node_id = node_id
        self.refresh_list()
        self.show_status(f"Node '{node_id}' saved.", "success")

    def refresh_list(self):
        self.node_listbox.delete(0, tk.END)
        for node_id in self.tree.nodes:
            self.node_listbox.insert(tk.END, node_id)

    def load_selected_node(self, event):
        selection = self.node_listbox.curselection()
        if not selection: return

        node_id = self.node_listbox.get(selection[0])
        self.current_node_id = node_id
        node = self.tree.get_node(node_id)

        # Clear & Fill
        self.entry_id.delete(0, tk.END)
        self.entry_id.insert(0, node.node_id)

        self.entry_speaker.delete(0, tk.END)
        self.entry_speaker.insert(0, node.speaker)

        self.text_content.delete("1.0", tk.END)
        self.text_content.insert("1.0", node.text)

        # Load linear flow field
        self.entry_next_node.delete(0, tk.END)
        if node.next_node_id:
            self.entry_next_node.insert(0, node.next_node_id)

    def clear_fields(self):
        """Clears all input fields to start creating a new node."""
        self.entry_id.delete(0, tk.END)
        self.entry_speaker.delete(0, tk.END)
        self.text_content.delete("1.0", tk.END)
        self.entry_next_node.delete(0, tk.END)
        self.current_node_id = None
        # Deselect any selected item in the listbox
        self.node_listbox.selection_clear(0, tk.END)

    def delete_node(self):
        """Deletes the currently selected node after confirmation."""
        if not self.current_node_id:
            self.show_status("Please select a node to delete.", "warning")
            return

        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete",
                                      f"Are you sure you want to delete node '{self.current_node_id}'?")
        if not confirm:
            return

        # Remove from tree
        if self.current_node_id in self.tree.nodes:
            del self.tree.nodes[self.current_node_id]
            self.show_status(f"Node '{self.current_node_id}' deleted.", "success")

            # Clear fields and refresh
            self.clear_fields()
            self.refresh_list()

    def export_json(self):
        self.tree.save_to_json()
        self.show_status("Exported to scripts/story_data.json", "success")

    def open_choice_window(self):
        if not self.current_node_id:
            self.show_status("Please save or select a Node first.", "warning")
            return

        node = self.tree.get_node(self.current_node_id)
        editing_index = [None]  # Mutable container for closure; None = adding, int = editing

        # Create Pop-up Window
        win = Toplevel(self.root)
        win.title(f"Choices for {node.node_id}")
        win.geometry("500x600")

        # List existing choices
        tk.Label(win, text="Existing Choices:").pack(anchor="w", padx=10, pady=5)

        choice_list = tk.Listbox(win, height=6)
        choice_list.pack(fill="x", padx=10)

        def refresh_choice_list():
            choice_list.delete(0, tk.END)
            for c in node.choices:
                req_text = " [LOCKED]" if c.get('requirements') else ""
                choice_list.insert(tk.END, f"-> {c['next_id']} : {c['text']}{req_text}")

        refresh_choice_list()

        # --- Edit / Delete buttons for existing choices ---
        list_btn_frame = tk.Frame(win)
        list_btn_frame.pack(fill="x", padx=10, pady=(2, 0))

        def edit_choice_action():
            selection = choice_list.curselection()
            if not selection:
                self.show_status("Select a choice to edit.", "warning")
                return
            idx = selection[0]
            choice = node.choices[idx]

            # Populate form fields with existing data
            c_text.delete(0, tk.END)
            c_text.insert(0, choice["text"])

            c_next.delete(0, tk.END)
            c_next.insert(0, choice["next_id"])

            c_effects.delete(0, tk.END)
            if choice.get("effects"):
                c_effects.insert(0, json.dumps(choice["effects"]))

            c_reqs.delete(0, tk.END)
            if choice.get("requirements"):
                c_reqs.insert(0, json.dumps(choice["requirements"]))

            editing_index[0] = idx
            form_label.config(text="--- Edit Choice ---")
            save_btn.config(text="Update Choice")

        def delete_choice_action():
            selection = choice_list.curselection()
            if not selection:
                self.show_status("Select a choice to delete.", "warning")
                return
            idx = selection[0]
            del node.choices[idx]
            refresh_choice_list()
            self.show_status("Choice deleted.", "success")

            # If we were editing the deleted choice, cancel the edit
            if editing_index[0] is not None:
                cancel_edit()

        tk.Button(list_btn_frame, text="Edit", command=edit_choice_action, bg="#add8e6").pack(side="left", padx=5)
        tk.Button(list_btn_frame, text="Delete", command=delete_choice_action, bg="#ffb3ba").pack(side="left", padx=5)

        # --- ADD / EDIT CHOICE FORM ---
        form_label = tk.Label(win, text="--- Add New Choice ---")
        form_label.pack(pady=10)

        tk.Label(win, text="Button Text:").pack()
        c_text = tk.Entry(win)
        c_text.pack()

        tk.Label(win, text="Target Node ID:").pack()
        c_next = tk.Entry(win)
        c_next.pack()

        tk.Label(win, text="Effects (JSON) e.g. {'gold': -5}").pack()
        c_effects = tk.Entry(win)
        c_effects.pack()

        tk.Label(win, text="Requirements (JSON) e.g. {'gold': 10}").pack()
        c_reqs = tk.Entry(win)
        c_reqs.pack()

        def parse_json(s):
            if not s: return {}
            try:
                return json.loads(s.replace("'", '"'))
            except Exception:
                messagebox.showerror("Error", f"Invalid JSON: {s}")
                return None

        def save_choice_action():
            txt = c_text.get()
            nxt = c_next.get()
            eff_str = c_effects.get()
            req_str = c_reqs.get()

            if not txt or not nxt:
                return

            real_effects = parse_json(eff_str)
            real_reqs = parse_json(req_str)
            if real_effects is None or real_reqs is None:
                return

            if editing_index[0] is not None:
                # Update existing choice in-place
                node.choices[editing_index[0]] = {
                    "text": txt,
                    "next_id": nxt,
                    "effects": real_effects,
                    "requirements": real_reqs
                }
                self.show_status("Choice updated.", "success")
            else:
                # Add new choice
                node.add_choice(txt, nxt, effects=real_effects, requirements=real_reqs)
                self.show_status("Choice added.", "success")

            refresh_choice_list()
            cancel_edit()

        def cancel_edit():
            """Reset form back to 'add new' mode."""
            editing_index[0] = None
            form_label.config(text="--- Add New Choice ---")
            save_btn.config(text="Add Choice")
            c_text.delete(0, tk.END)
            c_next.delete(0, tk.END)
            c_effects.delete(0, tk.END)
            c_reqs.delete(0, tk.END)

        btn_row = tk.Frame(win)
        btn_row.pack(pady=10)
        save_btn = tk.Button(btn_row, text="Add Choice", command=save_choice_action, bg="#90ee90")
        save_btn.pack(side="left", padx=5)
        tk.Button(btn_row, text="Cancel", command=cancel_edit, bg="#f0f0f0").pack(side="left", padx=5)

    def show_graph(self):
        """Passes the current tree to the visualizer module."""
        # Check if tree is empty
        if not self.tree.nodes:
            self.show_status("No nodes to visualize.", "warning")
            return

        try:
            visualizer.visualize_story(self.tree)
        except Exception as e:
            messagebox.showerror("Error", f"Graph failed: {e}")

    def open_variables_window(self):
        """Opens a window to manage global state variables and their initial values."""
        # Create Pop-up Window
        win = Toplevel(self.root)
        win.title("Global Variables Manager")
        win.geometry("500x450")

        # List existing variables
        lbl = tk.Label(win, text="Current Global Variables:")
        lbl.pack(anchor="w", padx=10, pady=5)

        var_list = tk.Listbox(win, height=8)
        var_list.pack(fill="x", padx=10)

        def refresh_var_list():
            """Refresh the listbox with current variables."""
            var_list.delete(0, tk.END)
            for var_name, var_value in self.tree.initial_state.items():
                var_list.insert(tk.END, f"{var_name}: {var_value}")

        refresh_var_list()

        # --- ADD/EDIT VARIABLE FORM ---
        tk.Label(win, text="--- Add/Edit Variable ---").pack(pady=10)

        tk.Label(win, text="Variable Name:").pack()
        v_name = tk.Entry(win)
        v_name.pack()

        tk.Label(win, text="Initial Value (number):").pack()
        v_value = tk.Entry(win)
        v_value.pack()

        def add_variable_action():
            """Add or update a variable in the initial state."""
            name = v_name.get().strip()
            value_str = v_value.get().strip()

            if not name:
                self.show_status("Variable name is required.", "warning")
                return

            if not value_str:
                self.show_status("Initial value is required.", "warning")
                return

            try:
                # Try to convert to int first, then float if that fails
                try:
                    value = int(value_str)
                except ValueError:
                    value = float(value_str)
            except ValueError:
                messagebox.showerror("Error", "Value must be a number!")
                return

            # Add to initial state
            self.tree.initial_state[name] = value
            # Also update current state if it doesn't exist
            if name not in self.tree.state:
                self.tree.state[name] = value

            refresh_var_list()

            # Clear inputs
            v_name.delete(0, tk.END)
            v_value.delete(0, tk.END)

            self.show_status(f"Variable '{name}' set to {value}", "success")

        def delete_variable_action():
            """Delete the selected variable."""
            selection = var_list.curselection()
            if not selection:
                self.show_status("Please select a variable to delete.", "warning")
                return

            selected_text = var_list.get(selection[0])
            var_name = selected_text.split(":")[0].strip()

            confirm = messagebox.askyesno("Confirm Delete",
                                          f"Are you sure you want to delete variable '{var_name}'?")
            if not confirm:
                return

            # Remove from initial state
            if var_name in self.tree.initial_state:
                del self.tree.initial_state[var_name]
            # Also remove from current state
            if var_name in self.tree.state:
                del self.tree.state[var_name]

            refresh_var_list()
            self.show_status(f"Variable '{var_name}' deleted.", "success")

        # Buttons
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Add/Update Variable", command=add_variable_action, bg="#90ee90").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete_variable_action, bg="#ffb3ba").pack(side="left", padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = NodeEditorApp(root)
    root.mainloop()