import os
import sys
import tkinter as tk
from tkinter import messagebox

# Add src to path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from src.models.nav_graph import NavigationGraph
from src.controllers.traffic_manager import TrafficManager
from src.controllers.fleet_manager import FleetManager
from src.gui.fleet_gui import FleetGUI
from src.utils.helpers import setup_logging

def main():
    # Set up logging
    logger = setup_logging()
    logger.info("Fleet Management System starting up")
    
    # Load nav_graph
    try:
        nav_graph_path = "D:\\full stack\\goat\\data\\nav_graph_2.json"
        logger.info(f"Loading navigation graph from {nav_graph_path}")
        nav_graph = NavigationGraph(nav_graph_path)
        logger.info(f"Loaded {len(nav_graph.vertices)} vertices and {len(nav_graph.lanes)} lanes")
    except Exception as e:
        logger.error(f"Failed to load navigation graph: {e}")
        messagebox.showerror("Error", f"Failed to load navigation graph: {e}")
        return
    
    # Create controllers
    traffic_manager = TrafficManager(logger)
    fleet_manager = FleetManager(nav_graph, traffic_manager, logger)
    
    # Create GUI
    root = tk.Tk()
    gui = FleetGUI(root, nav_graph, fleet_manager, traffic_manager, logger)
    
    # Handle window close
    def on_closing():
        logger.info("Shutting down Fleet Management System")
        gui.stop()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI
    logger.info("Starting GUI")
    root.mainloop()

if __name__ == "__main__":
    main()