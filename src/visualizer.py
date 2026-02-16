import networkx as nx
import matplotlib.pyplot as plt

def visualize_story(tree):
    """
    Generates a visual map of the dialogue tree using NetworkX and Matplotlib.
    """
    # 1. Create a Directed Graph (DiGraph)
    G = nx.DiGraph()

    # Track edge types for different visual styles
    choice_edges = []
    linear_edges = []
    edge_labels = {}

    # 2. Add Data to Graph
    for node_id, node in tree.nodes.items():
        G.add_node(node_id)

        # Add edges for linear flow (next_node_id)
        if node.next_node_id:
            G.add_edge(node_id, node.next_node_id)
            linear_edges.append((node_id, node.next_node_id))
            edge_labels[(node_id, node.next_node_id)] = "[auto]"

        # Add edges (arrows) for every choice
        for choice in node.choices:
            # We use the choice text as the label for the arrow
            # We truncate it to 15 chars so the graph isn't messy
            label_text = choice['text'][:15] + "..." if len(choice['text']) > 15 else choice['text']

            G.add_edge(node_id, choice['next_id'])
            choice_edges.append((node_id, choice['next_id']))
            edge_labels[(node_id, choice['next_id'])] = label_text

    # 3. Setup Layout — Kamada-Kawai produces cleaner, more stable results for DAGs
    #    Falls back to spring_layout if scipy is not installed
    try:
        pos = nx.kamada_kawai_layout(G)
    except ImportError:
        pos = nx.spring_layout(G, seed=42, k=0.5)

    # 4. Color nodes by role: end (red), branching (green), linear (blue)
    node_colors = []
    for nid in G.nodes():
        node = tree.nodes.get(nid)
        if node is None:
            # Orphan target referenced but not defined
            node_colors.append('#e0e0e0')    # gray
        elif not node.choices and not node.next_node_id:
            node_colors.append('#ffcdd2')    # red — end/leaf node
        elif node.choices:
            node_colors.append('#c8e6c9')    # green — branching node
        else:
            node_colors.append('#bbdefb')    # blue — linear flow

    # 5. Draw the Graph
    plt.figure(figsize=(12, 8))

    # Draw nodes with role-based colors
    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color=node_colors, edgecolors='black')

    # Draw labels (ID names inside circles)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

    # 6. Draw the Edges (Arrows)
    # Draw choice edges in gray (branching paths)
    if choice_edges:
        nx.draw_networkx_edges(G, pos, edgelist=choice_edges, edge_color='gray',
                               arrowstyle='->', arrowsize=20, width=2)

    # Draw linear flow edges in blue with dashed style (auto-advance)
    if linear_edges:
        nx.draw_networkx_edges(G, pos, edgelist=linear_edges, edge_color='blue',
                               arrowstyle='->', arrowsize=20, width=2, style='dashed')

    # Draw edge labels (Choice text and [auto] markers on the arrows)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    # 7. Add Legend (edges + node roles)
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='gray', linewidth=2, label='Choice (branching)'),
        Line2D([0], [0], color='blue', linewidth=2, linestyle='--', label='Linear flow (auto-advance)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#c8e6c9',
               markersize=12, markeredgecolor='black', label='Branching node'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#bbdefb',
               markersize=12, markeredgecolor='black', label='Linear node'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffcdd2',
               markersize=12, markeredgecolor='black', label='End node'),
    ]
    plt.legend(handles=legend_elements, loc='upper left')

    # 8. Show the Window
    plt.title("Story Logic Map")
    plt.axis('off') # Hide X/Y axis
    plt.tight_layout()
    plt.show()