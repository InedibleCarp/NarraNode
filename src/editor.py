import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel
import json
import narranode as engine
import visualizer as visualizer

class NodeEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NarraNode Editor")
        self.root.geometry("700x500")

        self.tree = engine.DialogueTree()
        self.current_node_id = None # Track what we are editing

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
        tk.Button(self.btn_frame, text="Manage Choices", command=self.open_choice_window, bg="#add8e6").pack(side="left", padx=5)

        # --- NEW BUTTON ---
        tk.Button(self.btn_frame, text="Show Map", command=self.show_graph, bg="#ffcccb").pack(side="left", padx=5)

        tk.Button(self.btn_frame, text="Export JSON", command=self.export_json).pack(side="right")

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
        messagebox.showinfo("Saved", f"Node '{node_id}' updated.")

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

    def export_json(self):
        self.tree.save_to_json()
        messagebox.showinfo("Export", "Saved to scripts/story_data.json")

    def open_choice_window(self):
        if not self.current_node_id:
            messagebox.showwarning("Warning", "Please save or select a Node first.")
            return

        node = self.tree.get_node(self.current_node_id)
        
        # Create Pop-up Window
        win = Toplevel(self.root)
        win.title(f"Choices for {node.node_id}")
        win.geometry("500x550") # Made slightly taller to fit new field

        # List existing choices
        lbl = tk.Label(win, text="Existing Choices:")
        lbl.pack(anchor="w", padx=10, pady=5)
        
        choice_list = tk.Listbox(win, height=6)
        choice_list.pack(fill="x", padx=10)

        for c in node.choices:
            # Display target + text. If it has requirements, show a little lock icon/text.
            req_text = " [LOCKED]" if c.get('requirements') else ""
            choice_list.insert(tk.END, f"-> {c['next_id']} : {c['text']}{req_text}")

        # --- ADD NEW CHOICE FORM ---
        tk.Label(win, text="--- Add New Choice ---").pack(pady=10)
        
        tk.Label(win, text="Button Text:").pack()
        c_text = tk.Entry(win)
        c_text.pack()

        tk.Label(win, text="Target Node ID:").pack()
        c_next = tk.Entry(win)
        c_next.pack()

        # Effects Field
        tk.Label(win, text="Effects (JSON) e.g. {'gold': -5}").pack()
        c_effects = tk.Entry(win)
        c_effects.pack()

        # NEW: Requirements Field
        tk.Label(win, text="Requirements (JSON) e.g. {'gold': 10}").pack()
        c_reqs = tk.Entry(win) # <--- The new input box
        c_reqs.pack()

        def add_choice_action():
            txt = c_text.get()
            nxt = c_next.get()
            eff_str = c_effects.get()
            req_str = c_reqs.get() # <--- Get the text
            
            if not txt or not nxt:
                return

            # Helper to safely parse JSON
            def parse_json(s):
                if not s: return {}
                try:
                    return json.loads(s.replace("'", '"'))
                except:
                    messagebox.showerror("Error", f"Invalid JSON: {s}")
                    return None

            real_effects = parse_json(eff_str)
            real_reqs = parse_json(req_str) # <--- Parse it

            # If JSON failed, stop
            if real_effects is None or real_reqs is None:
                return

            # Add to Backend
            node.add_choice(
                txt, 
                nxt, 
                effects=real_effects, 
                requirements=real_reqs # <--- Pass it to logic
            )
            
            # Refresh list
            req_display = " [LOCKED]" if real_reqs else ""
            choice_list.insert(tk.END, f"-> {nxt} : {txt}{req_display}")
            
            # Clear inputs
            c_text.delete(0, tk.END)
            c_next.delete(0, tk.END)
            c_effects.delete(0, tk.END)
            c_reqs.delete(0, tk.END)

        tk.Button(win, text="Add Choice", command=add_choice_action, bg="#90ee90").pack(pady=10)

    def show_graph(self):
        """Passes the current tree to the visualizer module."""
        # Check if tree is empty
        if not self.tree.nodes:
            messagebox.showwarning("Empty", "No nodes to visualize!")
            return
            
        try:
            visualizer.visualize_story(self.tree)
        except Exception as e:
            messagebox.showerror("Error", f"Graph failed: {e}")



if __name__ == "__main__":
    root = tk.Tk()
    app = NodeEditorApp(root)
    root.mainloop()