"""
Save and load utilities for the NFL Football Simulation
"""
import pickle


def save_franchise(franchise, filename="franchise_save.pkl"):
    """Save franchise to a pickle file"""
    with open(filename, "wb") as f:
        pickle.dump(franchise, f)
    print(f"Saved franchise to {filename}")


def load_franchise(filename="franchise_save.pkl"):
    """Load franchise from a pickle file"""
    try:
        with open(filename, "rb") as f:
            franchise = pickle.load(f)
        print(f"Loaded franchise from {filename}")
        return franchise
    except:
        return None
