import os
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from src.tools.rag_engine import RAGEngine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def visualize_chroma_embeddings():
    print("Initializing RAGEngine to connect to ChromaDB...")
    rag_engine = RAGEngine()
    print("RAGEngine initialized.")

    all_embeddings = []
    all_labels = []

    # Extract embeddings and labels from tasks collection
    print("Extracting embeddings from notion_tasks collection...")
    try:
        tasks_results = rag_engine.tasks_collection.get(include=['embeddings', 'metadatas'])
        if tasks_results and 'embeddings' in tasks_results and tasks_results['embeddings'] is not None:
            if len(tasks_results['embeddings']) > 0: # Explicitly check length
                all_embeddings.extend(tasks_results['embeddings'])
                all_labels.extend([f"task: {m.get('title', 'Untitled')}" for m in tasks_results['metadatas']])
                print(f"Extracted {len(tasks_results['embeddings'])} task embeddings.")
            else:
                print("No task embeddings found or collection is empty.")
        else:
            print("No 'embeddings' key in tasks_results or it's None.")
    except Exception as e:
        print(f"Error extracting task embeddings: {e}")

    # Extract embeddings and labels from routines collection
    print("Extracting embeddings from notion_routines collection...")
    try:
        routines_results = rag_engine.routines_collection.get(include=['embeddings', 'metadatas'])
        if routines_results and 'embeddings' in routines_results and routines_results['embeddings'] is not None:
            if len(routines_results['embeddings']) > 0: # Explicitly check length
                all_embeddings.extend(routines_results['embeddings'])
                all_labels.extend([f"routine: {m.get('task', 'Untitled')}" for m in routines_results['metadatas']])
                print(f"Extracted {len(routines_results['embeddings'])} routine embeddings.")
            else:
                print("No routine embeddings found or collection is empty.")
        else:
            print("No 'embeddings' key in routines_results or it's None.")
    except Exception as e:
        print(f"Error extracting routine embeddings: {e}")

    if not all_embeddings:
        print("No embeddings found to visualize.")
        return

    # Convert to numpy array
    embeddings_array = np.array(all_embeddings)
    print(f"Total embeddings for visualization: {embeddings_array.shape[0]}")

    # Apply t-SNE for dimensionality reduction
    print("Applying t-SNE for dimensionality reduction (this may take a while for large datasets)...")
    # Ensure perplexity is less than n_samples
    perplexity_val = min(30, embeddings_array.shape[0] - 1)
    if perplexity_val <= 0:
        print("Not enough samples for t-SNE with perplexity. Skipping t-SNE.")
        return

    tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity_val)
    reduced_embeddings = tsne.fit_transform(embeddings_array)
    print("t-SNE complete.")

    # Plotting
    plt.figure(figsize=(12, 10))
    
    # Separate task and routine points for coloring
    task_indices = [i for i, label in enumerate(all_labels) if label.startswith("task:")]
    routine_indices = [i for i, label in enumerate(all_labels) if label.startswith("routine:")]

    if task_indices:
        plt.scatter(reduced_embeddings[task_indices, 0], reduced_embeddings[task_indices, 1], label='Tasks', alpha=0.7, s=50)
    if routine_indices:
        plt.scatter(reduced_embeddings[routine_indices, 0], reduced_embeddings[routine_indices, 1], label='Routines', alpha=0.7, s=50)

    plt.title('ChromaDB Embeddings Visualization (t-SNE)')
    plt.xlabel('t-SNE Dimension 1')
    plt.ylabel('t-SNE Dimension 2')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    # Save the plot to a file
    plot_path = r"C:\Projects\agent_notion\chroma_embeddings_tsne.png"
    plt.savefig(plot_path)
    print(f"Visualization saved to {plot_path}")
    # plt.show() # Commented out for non-interactive environments

if __name__ == "__main__":
    visualize_chroma_embeddings()