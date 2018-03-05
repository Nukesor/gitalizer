"""Helper for plotting."""
import matplotlib.pyplot as plt


def plot_figure(path, fig):
    """Save a plot to a graph."""
    plt.xticks(rotation=30)
    plt.figure(figsize=(20, 10))
    fig.savefig(path)

    plt.close(fig)
