import time
import math
import logging

class Robot:
    STATUS_IDLE = "idle"
    STATUS_MOVING = "moving"
    STATUS_WAITING = "waiting"
    STATUS_CHARGING = "charging"
    STATUS_COMPLETED = "task_complete"
    STATUS_BLOCKED = "blocked"  # New status for when no alternative path exists
    
    def __init__(self, robot_id, current_vertex, nav_graph, logger=None):
        self.id = robot_id
        self.current_vertex = current_vertex
        self.destination_vertex = None
        self.path = []  # List of vertex indices to traverse
        self.original_path = []  # Store original path for reference
        self.current_lane = None  # (from_vertex, to_vertex)
        self.status = self.STATUS_IDLE
        self.nav_graph = nav_graph
        self.progress = 0.0  # Progress along current lane (0.0 to 1.0)
        self.color = self.generate_color()
        self.logger = logger or logging.getLogger(__name__)
        self.movement_start_time = None
        self.movement_total_time = 2.0  # Seconds to traverse a lane

        self.charging_start_time = None
        self.charging_total_time = 5.0  # Seconds required for charging
        self.charging_progress = 0.0
        
        # Track blocked lanes to avoid in path recalculation
        self.blocked_lanes = set()
        self.path_recalculation_attempts = 0
        self.max_recalculation_attempts = 3  # Limit recalculation attempts
        
        # Waiting reason tracking
        self.waiting_for_lane = False
        self.waiting_for_vertex = False
        
        # Register the robot at its current vertex
        self.log(f"Robot {self.id} spawned at {self.nav_graph.get_vertex_name(self.current_vertex)}")
    
    def generate_color(self):
        #Generate a unique color for the robot
        # Simple color generation based on ID
        colors = ["#FF5733", "#33FF57", "#3357FF", "#F033FF", "#FF33F0", 
                 "#33FFF0", "#F0FF33", "#5733FF", "#FF3357", "#57FF33"]
        return colors[self.id % len(colors)]
    
    def set_destination(self, destination_vertex):
        #Set the destination and calculate path
        self.destination_vertex = destination_vertex
        self.log(f"Robot {self.id} assigned to navigate to {self.nav_graph.get_vertex_name(destination_vertex)}")
        
        # Reset path tracking variables
        self.blocked_lanes = set()
        self.path_recalculation_attempts = 0
        
        # Calculate initial path
        self.calculate_path()
        
        if self.path:
            self.original_path = self.path.copy()  # Store original path
            self.status = self.STATUS_IDLE  # Will start moving in update
            return True
        else:
            self.log(f"Robot {self.id} could not find path to {self.nav_graph.get_vertex_name(destination_vertex)}")
            return False
    

    def calculate_path(self, avoid_lanes=None):
        #Calculate path using BFS with option to avoid certain lanes
        if self.current_vertex == self.destination_vertex:
            self.log(f"Robot {self.id} is already at destination vertex {self.destination_vertex}")
            self.path = []
            return
        
        if avoid_lanes is None:
            avoid_lanes = self.blocked_lanes
        
        queue = [(self.current_vertex, [])]
        visited = set([self.current_vertex])
        
        self.log(f"Robot {self.id} calculating path from {self.current_vertex} to {self.destination_vertex}")
        self.log(f"Avoiding lanes: {avoid_lanes}")
        
        while queue:
            vertex, path = queue.pop(0)
            
            # Check all connected vertices
            connected = self.nav_graph.get_connected_vertices(vertex)
            
            for next_vertex in connected:
                # Skip edges in the avoid_lanes set
                if (vertex, next_vertex) in avoid_lanes:
                    continue
                    
                if next_vertex == self.destination_vertex:
                    # Path found
                    final_path = path + [next_vertex]
                    self.path = final_path
                    self.log(f"Path found: {self.path}")
                    return
                
                if next_vertex not in visited:
                    visited.add(next_vertex)
                    queue.append((next_vertex, path + [next_vertex]))
        
        # No path found
        self.log(f"No path found from {self.current_vertex} to {self.destination_vertex} (avoiding {len(avoid_lanes)} lanes)")
        self.path = []
    
    def start_move_to_next_vertex(self, traffic_manager):
        #Attempt to start moving to the next vertex in the path
        if not self.path:
            # No path or already at destination
            if self.current_vertex == self.destination_vertex:
                self.status = self.STATUS_COMPLETED
                self.log(f"Robot {self.id} completed navigation to {self.nav_graph.get_vertex_name(self.destination_vertex)}")
            return False
        
        next_vertex = self.path[0]
        
        # First check if the destination vertex is already occupied
        if traffic_manager.is_vertex_occupied(next_vertex, self.id):
            self.status = self.STATUS_WAITING
            self.waiting_for_vertex = True
            self.waiting_for_lane = False
            occupying_robot = traffic_manager.get_vertex_occupying_robot(next_vertex)
            self.log(f"Robot {self.id} waiting for vertex {self.nav_graph.get_vertex_name(next_vertex)} - occupied by Robot {occupying_robot}")
            return False
        
        # Then request lane access
        if traffic_manager.request_lane_access(self, self.current_vertex, next_vertex):
            # Mark lane as occupied and begin movement
            self.current_lane = (self.current_vertex, next_vertex)
            self.status = self.STATUS_MOVING
            self.progress = 0.0
            self.movement_start_time = time.time()
            self.waiting_for_lane = False
            self.waiting_for_vertex = False
            self.log(f"Robot {self.id} moving from {self.nav_graph.get_vertex_name(self.current_vertex)} to {self.nav_graph.get_vertex_name(next_vertex)}")
            return True
        else:
            # Either lane or vertex is blocked
            self.status = self.STATUS_WAITING
            # Check specifically if it's the lane that's blocked
            if traffic_manager.is_lane_occupied(self.current_vertex, next_vertex):
                self.waiting_for_lane = True
                self.waiting_for_vertex = False
                occupying_robot = traffic_manager.get_occupying_robot(self.current_vertex, next_vertex)
                self.log(f"Robot {self.id} waiting for lane access from {self.nav_graph.get_vertex_name(self.current_vertex)} to {self.nav_graph.get_vertex_name(next_vertex)} - blocked by Robot {occupying_robot}")
            return False
        
    def update(self, traffic_manager, dt=None):
        """Update robot state"""
        # Register the robot's position with the traffic manager
        traffic_manager.occupy_vertex(self.id, self.current_vertex)
        
        # Handle charging state
        if self.status == self.STATUS_CHARGING:
            # If this is a new charging session, record start time
            if self.charging_start_time is None:
                self.charging_start_time = time.time()
                self.charging_progress = 0.0
                self.log(f"Robot {self.id} started charging at {self.nav_graph.get_vertex_name(self.current_vertex)}")
            
            # Update charging progress
            if dt is None:
                # Calculate time-based progress
                current_time = time.time()
                elapsed = current_time - self.charging_start_time
                self.charging_progress = min(1.0, elapsed / self.charging_total_time)
            else:
                # Use provided dt (for fixed time step)
                self.charging_progress += dt / self.charging_total_time
                self.charging_progress = min(1.0, self.charging_progress)

            # If charging is complete, change to idle status
            if self.charging_progress >= 1.0:
                self.status = self.STATUS_IDLE
                self.charging_start_time = None
                self.charging_progress = 0.0
                self.log(f"Robot {self.id} finished charging at {self.nav_graph.get_vertex_name(self.current_vertex)}")
            
            # If the robot has a path (assigned during charging), don't exit yet, wait until charging is done
            return
        
        # If blocked, stay blocked until user intervention
        if self.status == self.STATUS_BLOCKED:
            return
        
        # If waiting, periodically check if lane/vertex is now available
        if self.status == self.STATUS_WAITING and self.path:
            next_vertex = self.path[0]
            
            # Check if we're waiting for a vertex and if it's now free
            if self.waiting_for_vertex and not traffic_manager.is_vertex_occupied(next_vertex, self.id):
                self.waiting_for_vertex = False
                self.movement_start_time = None  # Reset timer
                self.log(f"Vertex {next_vertex} is now free. Attempting to move.")
                self.start_move_to_next_vertex(traffic_manager)
                return
                
            # Check if we're waiting for a lane and if it's now free
            if self.waiting_for_lane and not traffic_manager.is_lane_occupied(self.current_vertex, next_vertex):
                self.waiting_for_lane = False
                self.movement_start_time = None  # Reset timer
                self.log(f"Lane from {self.current_vertex} to {next_vertex} is now free. Attempting to move.")
                self.start_move_to_next_vertex(traffic_manager)
                return
                
            # If we're waiting but haven't set a specific reason, check both
            if not self.waiting_for_lane and not self.waiting_for_vertex:
                if not traffic_manager.is_lane_occupied(self.current_vertex, next_vertex) and \
                   not traffic_manager.is_vertex_occupied(next_vertex, self.id):
                    self.movement_start_time = None  # Reset timer
                    self.log(f"Path to {next_vertex} is now clear. Attempting to move.")
                    self.start_move_to_next_vertex(traffic_manager)
                else:
                    # Initialize the waiting timer if not already set
                    if self.movement_start_time is None:
                        self.movement_start_time = time.time()
                        self.log(f"Robot {self.id} waiting for path to {next_vertex} to become available")
            return
        
        # If idle with a path, try to start moving
        if self.status == self.STATUS_IDLE and self.path:
            self.start_move_to_next_vertex(traffic_manager)
            return
        
        # If moving, update progress
        if self.status == self.STATUS_MOVING:
            if dt is None:
                # Calculate time-based progress
                current_time = time.time()
                elapsed = current_time - self.movement_start_time
                self.progress = min(1.0, elapsed / self.movement_total_time)
            else:
                # Use provided dt (for fixed time step)
                self.progress += dt / self.movement_total_time
                self.progress = min(1.0, self.progress)
            
            # Check if movement is complete
            if self.progress >= 1.0:
                # Update position
                from_vertex, to_vertex = self.current_lane
                
                # Release the current vertex since we're leaving it
                traffic_manager.release_vertex(self.current_vertex)
                
                # Release the lane and get the next robot to notify (if any)
                success, next_robot_id = traffic_manager.release_lane(from_vertex, to_vertex)
                
                # Update our position
                self.current_vertex = to_vertex
                self.current_lane = None
                self.path.pop(0)  # Remove the vertex we just reached
                self.status = self.STATUS_IDLE
                
                # Register at the new vertex
                traffic_manager.occupy_vertex(self.id, self.current_vertex)
                
                self.log(f"Robot {self.id} arrived at {self.nav_graph.get_vertex_name(self.current_vertex)}")
                
                # If at destination, mark as complete
                if not self.path and self.current_vertex == self.destination_vertex:
                    self.status = self.STATUS_COMPLETED
                    self.log(f"Robot {self.id} completed navigation to {self.nav_graph.get_vertex_name(self.destination_vertex)}")
    
    def get_current_position(self):
        #Get current coordinates based on progress along lane
        if self.status == self.STATUS_MOVING and self.current_lane:
            from_vertex, to_vertex = self.current_lane
            from_coords = self.nav_graph.get_vertex_coords(from_vertex)
            to_coords = self.nav_graph.get_vertex_coords(to_vertex)
            
            # Interpolate position
            x = from_coords[0] + (to_coords[0] - from_coords[0]) * self.progress
            y = from_coords[1] + (to_coords[1] - from_coords[1]) * self.progress
            return (x, y)
        else:
            return self.nav_graph.get_vertex_coords(self.current_vertex)
    
    def get_blocking_info(self, traffic_manager):
        #Get info about what's blocking this robot
        if self.status == self.STATUS_WAITING and self.path:
            next_vertex = self.path[0]
            
            # Check if waiting for vertex
            if traffic_manager.is_vertex_occupied(next_vertex, self.id):
                blocking_robot_id = traffic_manager.get_vertex_occupying_robot(next_vertex)
                if blocking_robot_id is not None:
                    return {
                        "blocked_vertex": next_vertex,
                        "blocking_robot": blocking_robot_id
                    }
            
            # Check if waiting for lane
            if traffic_manager.is_lane_occupied(self.current_vertex, next_vertex):
                blocking_robot_id = traffic_manager.get_occupying_robot(self.current_vertex, next_vertex)
                if blocking_robot_id is not None:
                    return {
                        "blocked_lane": (self.current_vertex, next_vertex),
                        "blocking_robot": blocking_robot_id
                    }
        return None
    
    def get_status_text(self):
        #Get detailed status text for UI display
        if self.status == self.STATUS_WAITING:
            if self.waiting_for_vertex:
                return "Waiting - Vertex Occupied"
            elif self.waiting_for_lane:
                return "Waiting - Lane Blocked"
            else:
                return "Waiting - Path Blocked"
        elif self.status == self.STATUS_BLOCKED:
            return "Blocked - No Alternative"
        elif self.status == self.STATUS_IDLE:
            return "Idle"
        elif self.status == self.STATUS_MOVING:
            return "Moving"
        elif self.status == self.STATUS_CHARGING:
            return f"Charging - {int(self.charging_progress * 100)}%"
        elif self.status == self.STATUS_COMPLETED:
            return "Task Complete"
        return self.status
    
    def log(self, message):
        #Log robot action
        if self.logger:
            return