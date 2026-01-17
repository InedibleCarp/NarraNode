import networkx as nx
import matplotlib.pyplot as plt

def visualize_story(tree):
    """
    Generates a visual map of the dialogue tree using NetworkX and Matplotlib.
    """
    # 1. Create a Directed Graph (DiGraph)
    G = nx.DiGraph()

    # 2. Add Data to Graph
    for node_id, node in tree.nodes.items():
        G.add_node(node_id)
        
        # Add edges (arrows) for every choice
        for choice in node.choices:
            # We use the choice text as the label for the arrow
            # We truncate it to 15 chars so the graph isn't messy
            label_text = choice['text'][:15] + "..." if len(choice['text']) > 15 else choice['text']
            
            G.add_edge(node_id, choice['next_id'], label=label_text)

    # 3. Setup Layout (Spring layout tries to space nodes out naturally)
    pos = nx.spring_layout(G, seed=42, k=0.5) 

    # 4. Draw the Nodes
    plt.figure(figsize=(12, 8)) # Window size
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color='lightblue', edgecolors='black')
    
    # Draw labels (ID names inside circles)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

    # 5. Draw the Edges (Arrows)
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrowstyle='->', arrowsize=20)
    
    # Draw edge labels (Choice text on the arrows)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    # 6. Show the Window
    plt.title("Story Logic Map")
    plt.axis('off') # Hide X/Y axis
    plt.show()