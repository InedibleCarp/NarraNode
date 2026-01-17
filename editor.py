import tkinter as tk
from tkinter import messagebox, ttk
import narranode as engine

class NodeEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NarraNode Editor")
        self.root.geometry("600x400")

        # 1. Initialize the Logic Engine
        self.tree = engine.DialogueTree()
        
        # --- GUI LAYOUT ---
        
        # Left Panel (Node List)
        self.left_frame = tk.Frame(root, width=200, bg="#e0e0e0")
        self.left_frame.pack(side="left", fill="y")
        
        tk.Label(self.left_frame, text="Nodes List", bg="#e0e0e0").pack(pady=5)
        self.node_listbox = tk.Listbox(self.left_frame)
        self.node_listbox.pack(fill="both", expand=True, padx=5)
        self.node_listbox.bind('<<ListboxSelect>>', self.load_selected_node)
        
        # Right Panel (Editor)
        self.right_frame = tk.Frame(root, padx=10, pady=10)
        self.right_frame.pack(side="right", fill="both", expand=True)

        # Fields
        tk.Label(self.right_frame, text="Node ID:").grid(row=0, column=0, sticky="w")
        self.entry_id = tk.Entry(self.right_frame)
        self.entry_id.grid(row=0, column=1, sticky="ew")

        tk.Label(self.right_frame, text="Speaker:").grid(row=1, column=0, sticky="w")
        self.entry_speaker = tk.Entry(self.right_frame)
        self.entry_speaker.grid(row=1, column=1, sticky="ew")

        tk.Label(self.right_frame, text="Dialogue Text:").grid(row=2, column=0, sticky="nw")
        self.text_content = tk.Text(self.right_frame, height=5, width=40)
        self.text_content.grid(row=2, column=1)

        # Buttons
        self.btn_frame = tk.Frame(self.right_frame)
        self.btn_frame.grid(row=4, column=1, pady=10, sticky="e")
        
        tk.Button(self.btn_frame, text="Save Node", command=self.save_node).pack(side="left", padx=5)
        tk.Button(self.btn_frame, text="Export JSON", command=self.export_json).pack(side="left")

        # Configure Grid
        self.right_frame.columnconfigure(1, weight=1)

    def save_node(self):
        """Creates a Node object from the UI fields and adds it to the Tree"""
        node_id = self.entry_id.get()
        speaker = self.entry_speaker.get()
        text = self.text_content.get("1.0", tk.END).strip()

        if not node_id:
            messagebox.showerror("Error", "Node ID is required!")
            return

        # Create using the Logic Class from your other file
        new_node = engine.DialogueNode(node_id, speaker, text)
        self.tree.add_node(new_node)
        
        self.refresh_list()
        messagebox.showinfo("Success", f"Node '{node_id}' saved to memory.")

    def refresh_list(self):
        """Updates the sidebar listbox"""
        self.node_listbox.delete(0, tk.END)
        for node_id in self.tree.nodes:
            self.node_listbox.insert(tk.END, node_id)

    def load_selected_node(self, event):
        """When you click a list item, fill the form"""
        selection = self.node_listbox.curselection()
        if not selection: return
        
        node_id = self.node_listbox.get(selection[0])
        node = self.tree.get_node(node_id)
        
        # Clear fields
        self.entry_id.delete(0, tk.END)
        self.entry_speaker.delete(0, tk.END)
        self.text_content.delete("1.0", tk.END)
        
        # Fill fields
        self.entry_id.insert(0, node.node_id)
        self.entry_speaker.insert(0, node.speaker)
        self.text_content.insert("1.0", node.text)

    def export_json(self):
        self.tree.save_to_json()
        messagebox.showinfo("Export", "Saved to story_data.json")

if __name__ == "__main__":
    root = tk.Tk()
    app = NodeEditorApp(root)
    root.mainloop()