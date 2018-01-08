"""Helper for plotting."""
import matplotlib.pyplot as plt


def plot_figure(path, ax):
    """Save a plot to a graph."""
    plt.xticks(rotation=30)

    plt.figure(figsize=(20, 10))
    fig = ax.get_figure()
    fig.savefig(path)

    plt.close(fig)
