# NarraNode

**NarraNode** is a lightweight, Python-based dialogue management tool designed for game developers. It allows users to create branching narratives with conditional logic (RPG mechanics) and export them to JSON for integration into game engines like Unreal Engine 5 or Unity.

## Features
* **Visual Editor:** A Tkinter-based GUI to create and edit dialogue nodes.
* **Branching Logic:** Create infinite choices linking to other nodes.
* **State Management:**
    * **Effects:** Choices can modify player stats (e.g., `{"gold": -10}`).
    * **Requirements:** Choices can be locked based on stats (e.g., `{"gold": 50}` to unlock).
* **JSON Export:** Saves data in a structured format ready for Data Tables.
* **CLI Play Mode:** built-in text engine to playtest your story in the terminal.

## Installation
NarraNode uses the standard Python library. No external dependencies are required.

1.  Clone or download the repository.
2.  Ensure you have Python 3.x installed.

## Usage

### 1. The Editor (GUI)
Run the editor to build your story visually.
```bash
python editor.py

```

* **Create Node:** Enter an ID, Speaker, and Text, then click Save.
* **Manage Choices:** Select a node and click "Manage Choices" to add branches.
* **Effects:** Enter JSON, e.g., `{'hp': -10}`.
* **Requirements:** Enter JSON, e.g., `{'intellect': 5}`.


* **Export:** Click "Export JSON" to save your work to `story_data.json`.

### 2. The Playtest Engine (CLI)

Test your story logic directly in the terminal.

```bash
python narranode.py

```

## Project Structure

* `narranode.py` - The backend logic (Models) and text-based game engine.
* `editor.py` - The frontend application (View).
* `story_data.json` - The database file (generated upon use).

## Integration Guide

To use in Unreal Engine 5:

1. Create a **Struct** matching the JSON fields (ID, Speaker, Text, Choices).
2. Import `story_data.json` as a **DataTable** using that Struct.