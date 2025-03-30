import tkinter as tk
from tkinter import ttk, messagebox
import math
import time
import threading

class FleetGUI:
    # Constants
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 600
    VERTEX_RADIUS = 15
    ROBOT_RADIUS = 10
    CHARGER_COLOR = "#FFD700"  # Gold
    VERTEX_COLOR = "#808080"   # Gray
    LANE_COLOR = "#A0A0A0"     # Light Gray
    SELECTION_COLOR = "#FF0000"  # Red
    
    def __init__(self, root, nav_graph, fleet_manager, traffic_manager, logger):
        self.root = root
        self.nav_graph = nav_graph
        self.fleet_manager = fleet_manager
        self.traffic_manager = traffic_manager
        self.logger = logger
        
        # Set up the window
        self.root.title("Fleet Management System")
        self.root.geometry(f"{self.CANVAS_WIDTH + 200}x{self.CANVAS_HEIGHT}")
        
        # Scale factors for drawing nav_graph
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for visualization
        self.canvas = tk.Canvas(self.main_frame, width=self.CANVAS_WIDTH, height=self.CANVAS_HEIGHT, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create side panel for controls and info
        self.side_panel = ttk.Frame(self.main_frame, width=200)
        self.side_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add components to side panel
        ttk.Label(self.side_panel, text="Fleet Management System", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Status section
        ttk.Separator(self.side_panel).pack(fill=tk.X, pady=5)
        ttk.Label(self.side_panel, text="Robot Status", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.status_frame = ttk.Frame(self.side_panel)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create status indicators
        self.status_labels = {}
        statuses = [
            ("idle", "Idle"),
            ("moving", "Moving"),
            ("waiting", "Waiting"),
            ("charging", "Charging"),
            ("task_complete", "Complete")
        ]
        
        for status_key, status_text in statuses:
            frame = ttk.Frame(self.status_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{status_text}:").pack(side=tk.LEFT)
            self.status_labels[status_key] = ttk.Label(frame, text="0")
            self.status_labels[status_key].pack(side=tk.RIGHT)
        
        # Instructions section
        ttk.Separator(self.side_panel).pack(fill=tk.X, pady=5)
        ttk.Label(self.side_panel, text="Instructions", font=("Arial", 10, "bold")).pack(pady=5)
        
        instructions = [
            "• Click on a vertex to spawn a robot",
            "• Click on a robot, then a vertex to assign task",
            "• Golden vertices are charging stations"
        ]
        
        for instruction in instructions:
            ttk.Label(self.side_panel, text=instruction, wraplength=180).pack(anchor=tk.W, padx=5)
        
        # Current selection info
        ttk.Separator(self.side_panel).pack(fill=tk.X, pady=5)
        ttk.Label(self.side_panel, text="Selection", font=("Arial", 10, "bold")).pack(pady=5)
        self.selection_info = ttk.Label(self.side_panel, text="None selected", wraplength=180)
        self.selection_info.pack(padx=5, pady=5)
        
        # Clear selection button
        ttk.Button(self.side_panel, text="Clear Selection", command=self.clear_selection).pack(pady=5)
        
        # Initialize selection state
        self.selected_robot = None
        
        # Calculate scaling factors based on nav_graph
        self.calculate_scaling_factors()
        
        # Set up canvas interactions
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Start update loop
        self.running = True
        self.last_update_time = time.time()
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    
    def calculate_scaling_factors(self):
        #Calculate scaling factors to position the nav_graph on the canvas
        # Get min and max coordinates to understand the graph dimensions
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        print("Calculating scaling factors for graph...")
        vertex_count = 0
        
        for vertex_index in self.nav_graph.vertex_map:
            coords = self.nav_graph.get_vertex_coords(vertex_index)
            if not coords:
                print(f"Warning: Vertex {vertex_index} has no coordinates")
                continue
                
            print(f"Vertex {vertex_index} coords: {coords}")
            min_x = min(min_x, coords[0])
            min_y = min(min_y, coords[1])
            max_x = max(max_x, coords[0])
            max_y = max(max_y, coords[1])
            vertex_count += 1
        
        if vertex_count == 0:
            print("Warning: No vertices with coordinates found")
            self.scale_x = 1.0
            self.scale_y = 1.0
            self.offset_x = 50
            self.offset_y = 50
            return
        
        print(f"Graph bounds: ({min_x}, {min_y}) to ({max_x}, {max_y})")
        
        # Determine graph dimensions
        graph_width = max_x - min_x
        graph_height = max_y - min_y
        
        # Calculate scaling factors to fit the graph on the canvas
        # Leave some margin around the edges
        margin = 50
        canvas_usable_width = self.CANVAS_WIDTH - 2 * margin
        canvas_usable_height = self.CANVAS_HEIGHT - 2 * margin
        
        # Prevent division by zero
        if graph_width > 0:
            self.scale_x = canvas_usable_width / graph_width
        else:
            self.scale_x = 1.0
            
        if graph_height > 0:
            self.scale_y = canvas_usable_height / graph_height
        else:
            self.scale_y = 1.0
        
        # Use the smaller scale to maintain aspect ratio
        scale = min(self.scale_x, self.scale_y)
        self.scale_x = scale
        self.scale_y = scale
        
        # Set offsets to center the graph
        self.offset_x = margin + (canvas_usable_width - graph_width * scale) / 2 - min_x * scale
        self.offset_y = margin + (canvas_usable_height - graph_height * scale) / 2 - min_y * scale
        
        print(f"Scale factors: ({self.scale_x}, {self.scale_y})")
        print(f"Centering offsets: ({self.offset_x}, {self.offset_y})")

    def world_to_canvas(self, world_x, world_y):
        #Convert world coordinates to canvas coordinates
        canvas_x = world_x * self.scale_x + self.offset_x
        canvas_y = world_y * self.scale_y + self.offset_y
        return canvas_x, canvas_y
    
    def draw_nav_graph(self):
        """Draw the navigation graph on the canvas"""
        # Clear canvas
        self.canvas.delete("all")
        
        #print("Drawing navigation graph...")
        
        # Draw lanes
        for lane in self.nav_graph.lanes:
            from_vertex, to_vertex = lane[0], lane[1]
            
            from_coords = self.nav_graph.get_vertex_coords(from_vertex)
            to_coords = self.nav_graph.get_vertex_coords(to_vertex)
            
            if not from_coords or not to_coords:
                print(f"Missing coordinates for lane {from_vertex} -> {to_vertex}")
                continue
                
            from_x, from_y = self.world_to_canvas(*from_coords)
            to_x, to_y = self.world_to_canvas(*to_coords)
            
            # Check if lane is occupied
            lane_color = self.LANE_COLOR
            lane_width = 2
            
            if self.traffic_manager.is_lane_occupied(from_vertex, to_vertex):
                # Occupied lane
                lane_color = "#FF6666"  # Light red for occupied lanes
                lane_width = 3  # Thicker lines for occupied lanes
                
                # Get the occupying robot's ID
                robot_id = self.traffic_manager.get_occupying_robot(from_vertex, to_vertex)
                
                # Draw direction arrow
                self.draw_arrow(from_x, from_y, to_x, to_y, lane_color, lane_width)
                
                # Draw small label with robot ID
                mid_x = (from_x + to_x) / 2
                mid_y = (from_y + to_y) / 2
                self.canvas.create_oval(mid_x-8, mid_y-8, mid_x+8, mid_y+8, fill="white")
                self.canvas.create_text(mid_x, mid_y, text=str(robot_id), font=("Arial", 7, "bold"))
                
                # Check if there are robots waiting for this lane and visualize the queue
                queue_length = self.traffic_manager.get_queue_length(from_vertex, to_vertex)
                if queue_length > 0:
                    # Draw a small indicator showing queue length
                    offset_x = (to_y - from_y) * 0.1  # Perpendicular offset
                    offset_y = -(to_x - from_x) * 0.1
                    self.canvas.create_oval(
                        mid_x + offset_x - 10, 
                        mid_y + offset_y - 10, 
                        mid_x + offset_x + 10, 
                        mid_y + offset_y + 10, 
                        fill="#FFA500"  # Orange for waiting
                    )
                    self.canvas.create_text(mid_x + offset_x, mid_y + offset_y, 
                                        text=f"{queue_length}", font=("Arial", 7, "bold"))
            else:
                # Free lane - normal line
                self.canvas.create_line(from_x, from_y, to_x, to_y, fill=lane_color, width=lane_width)
        
        # Draw vertices (rest of method unchanged)
        for vertex_index in self.nav_graph.vertex_map:
            coords = self.nav_graph.get_vertex_coords(vertex_index)
            if not coords:
                print(f"Missing coordinates for vertex {vertex_index}")
                continue
                
            canvas_x, canvas_y = self.world_to_canvas(*coords)
            
            # Determine color based on whether it's a charger
            vertex_color = self.CHARGER_COLOR if self.nav_graph.is_charger(vertex_index) else self.VERTEX_COLOR
            
            # Check if vertex has a robot
            robot = self.fleet_manager.get_robot_at_vertex(vertex_index)
            outline_color = "black"
            outline_width = 1
            
            if robot and robot.id == self.selected_robot:
                outline_color = self.SELECTION_COLOR
                outline_width = 3
            
            # Draw the vertex
            self.canvas.create_oval(
                canvas_x - self.VERTEX_RADIUS, canvas_y - self.VERTEX_RADIUS,
                canvas_x + self.VERTEX_RADIUS, canvas_y + self.VERTEX_RADIUS,
                fill=vertex_color, outline=outline_color, width=outline_width, tags=f"vertex_{vertex_index}"
            )
            
            # Add vertex name
            vertex_name = self.nav_graph.get_vertex_name(vertex_index)
            if vertex_name:
                self.canvas.create_text(canvas_x, canvas_y, text=vertex_name, font=("Arial", 8))

    def draw_arrow(self, from_x, from_y, to_x, to_y, color, width=2):
        """Draw an arrow to indicate lane direction and occupancy"""
        # Calculate direction vector
        dx = to_x - from_x
        dy = to_y - from_y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1e-6:
            return
        
        # Normalize
        dx /= length
        dy /= length
        
        # Draw the line
        self.canvas.create_line(from_x, from_y, to_x, to_y, fill=color, width=width, arrow=tk.LAST)
    
    def draw_robots(self):
        #Draw all robots on the canvas
        for robot_id, robot in self.fleet_manager.robots.items():
            pos = robot.get_current_position()
            if pos:
                canvas_x, canvas_y = self.world_to_canvas(*pos)
                
                # Different outline for selected robot
                outline_color = self.SELECTION_COLOR if robot_id == self.selected_robot else "black"
                outline_width = 3 if robot_id == self.selected_robot else 1
                
                # Draw the robot
                self.canvas.create_oval(
                    canvas_x - self.ROBOT_RADIUS, canvas_y - self.ROBOT_RADIUS,
                    canvas_x + self.ROBOT_RADIUS, canvas_y + self.ROBOT_RADIUS,
                    fill=robot.color, outline=outline_color, width=outline_width, tags=f"robot_{robot_id}"
                )
                
                # Draw robot ID
                self.canvas.create_text(canvas_x, canvas_y, text=str(robot_id), font=("Arial", 8, "bold"))
                
                # Draw status indicator
                status_color = {
                    robot.STATUS_IDLE: "#808080",      # Gray
                    robot.STATUS_MOVING: "#00FF00",    # Green
                    robot.STATUS_WAITING: "#FFA500",   # Orange
                    robot.STATUS_CHARGING: "#FFD700",  # Gold
                    robot.STATUS_COMPLETED: "#00FFFF"  # Cyan
                }.get(robot.status, "#808080")
                
                self.canvas.create_rectangle(
                    canvas_x - self.ROBOT_RADIUS, canvas_y - self.ROBOT_RADIUS - 8,
                    canvas_x + self.ROBOT_RADIUS, canvas_y - self.ROBOT_RADIUS - 3,
                    fill=status_color, outline="black"
                )
    
    def update_gui(self):
        #Update the GUI components
        # Redraw the nav_graph and robots
        self.draw_nav_graph()
        self.draw_robots()
        
        # Update status counts
        status_counts = self.fleet_manager.get_robot_status_count()
        for status, count in status_counts.items():
            if status in self.status_labels:
                self.status_labels[status].config(text=str(count))
        
        # Update selection info
        if self.selected_robot is not None:
            if self.selected_robot in self.fleet_manager.robots:
                robot = self.fleet_manager.robots[self.selected_robot]
                status_text = f"Robot {robot.id}\n"
                status_text += f"Status: {robot.status}\n"
                status_text += f"Position: {self.nav_graph.get_vertex_name(robot.current_vertex)}\n"
                
                if robot.destination_vertex is not None:
                    status_text += f"Destination: {self.nav_graph.get_vertex_name(robot.destination_vertex)}"
                
                self.selection_info.config(text=status_text)
            else:
                self.selected_robot = None
                self.selection_info.config(text="None selected")
        else:
            self.selection_info.config(text="None selected")
    
    def update_loop(self):
        #Main update loop for simulation
        update_interval = 1.0 / 30  # Target 30 FPS
        
        while self.running:
            current_time = time.time()
            dt = current_time - self.last_update_time
            self.last_update_time = current_time
            
            # Update fleet manager (and robots)
            self.fleet_manager.update(dt)
            
            # Update GUI on the main thread
            self.root.after(0, self.update_gui)
            
            # Sleep to maintain target frame rate
            time.sleep(max(0, update_interval - (time.time() - current_time)))
    
    def on_canvas_click(self, event):
        #Handle clicks on the canvas
        canvas_x, canvas_y = event.x, event.y
        
        # Check if a robot was clicked
        for robot_id, robot in self.fleet_manager.robots.items():
            pos = robot.get_current_position()
            if pos:
                robot_canvas_x, robot_canvas_y = self.world_to_canvas(*pos)
                
                # Check if click is within robot
                dx = canvas_x - robot_canvas_x
                dy = canvas_y - robot_canvas_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= self.ROBOT_RADIUS:
                    self.selected_robot = robot_id
                    self.logger.info(f"Selected Robot {robot_id}")
                    self.update_gui()
                    return
        
        # Check if a vertex was clicked
        for vertex_index in self.nav_graph.vertex_map:
            coords = self.nav_graph.get_vertex_coords(vertex_index)
            vertex_canvas_x, vertex_canvas_y = self.world_to_canvas(*coords)
                
            # Check if click is within vertex
            dx = canvas_x - vertex_canvas_x
            dy = canvas_y - vertex_canvas_y
            distance = math.sqrt(dx*dx + dy*dy)
                
            if distance <= self.VERTEX_RADIUS:
                # If a robot is selected, assign task
                if self.selected_robot is not None:
                    robot = self.fleet_manager.robots.get(self.selected_robot)
                    if robot:
                        success = self.fleet_manager.assign_task(self.selected_robot, vertex_index)
                        if success:
                            messagebox.showinfo("Task Assigned", 
                                                f"Robot {self.selected_robot} assigned to navigate to {self.nav_graph.get_vertex_name(vertex_index)}")
                        else:
                            messagebox.showwarning("Task Assignment Failed", 
                                                f"Could not assign Robot {self.selected_robot} to navigate to {self.nav_graph.get_vertex_name(vertex_index)}")
                        self.clear_selection()
                else:
                    # Spawn a new robot
                    robot = self.fleet_manager.spawn_robot(vertex_index)
                    if robot:
                        messagebox.showinfo("Robot Spawned", 
                                            f"Robot {robot.id} spawned at {self.nav_graph.get_vertex_name(vertex_index)}")
                    
                self.update_gui()
                return
    
    def clear_selection(self):
        #Clear the current selection
        self.selected_robot = None
        self.update_gui()
    
    def stop(self):
        #Stop the update loop
        self.running = False
        if self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)