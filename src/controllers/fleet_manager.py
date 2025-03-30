import logging

class FleetManager:
    def __init__(self, nav_graph, traffic_manager, logger=None):
        self.robots = {}  # Dictionary of robot_id: Robot object
        self.nav_graph = nav_graph
        self.traffic_manager = traffic_manager
        self.next_robot_id = 0
        self.logger = logger or logging.getLogger(__name__)
    
    def spawn_robot(self, vertex_index):
        """Spawn a new robot at the specified vertex"""
        from src.models.robot import Robot
        
        # Check if the vertex exists
        if vertex_index not in self.nav_graph.vertex_map:
            self.logger.error(f"Cannot spawn robot at invalid vertex {vertex_index}")
            return None
        
        # Create the robot
        robot = Robot(self.next_robot_id, vertex_index, self.nav_graph, self.logger)
        self.robots[self.next_robot_id] = robot
        
        self.logger.info(f"Spawned Robot {self.next_robot_id} at vertex {vertex_index} ({self.nav_graph.get_vertex_name(vertex_index)})")
        
        # Increment robot ID for next spawn
        self.next_robot_id += 1
        
        return robot
    
    def assign_task(self, robot_id, destination_vertex):
        """Assign a navigation task to a robot"""
        if robot_id not in self.robots:
            self.logger.error(f"Cannot assign task to non-existent robot {robot_id}")
            return False
        
        if destination_vertex not in self.nav_graph.vertex_map:
            self.logger.error(f"Cannot assign task with invalid destination vertex {destination_vertex}")
            return False
        
        robot = self.robots[robot_id]
        success = robot.set_destination(destination_vertex)
        
        if success:
            self.logger.info(f"Assigned Robot {robot_id} to navigate to vertex {destination_vertex} ({self.nav_graph.get_vertex_name(destination_vertex)})")
            self.logger.info(f"Path calculated: {robot.path}")
        else:
            self.logger.warning(f"Failed to assign Robot {robot_id} to navigate to vertex {destination_vertex}")
        
        return success
    
    def update(self, dt=None):
        """Update all robots"""
        for robot_id, robot in self.robots.items():
            robot.update(self.traffic_manager, dt)
        
    
        self.get_robot_status_count()
    
    def get_robot_at_vertex(self, vertex_index):
        """Get the first robot found at the specified vertex"""
        for robot in self.robots.values():
            if robot.current_vertex == vertex_index and robot.status != robot.STATUS_MOVING:
                return robot
        return None
    
    def get_robot_status_count(self):
        """Count robots in each status"""
        counts = {
            "idle": 0,
            "moving": 0,
            "waiting": 0,
            "charging": 0,
            "task_complete": 0
        }
        
        for robot in self.robots.values():
            if robot.status == robot.STATUS_IDLE:
                counts["idle"] += 1
            elif robot.status == robot.STATUS_MOVING:
                counts["moving"] += 1
            elif robot.status == robot.STATUS_WAITING:
                counts["waiting"] += 1
            elif robot.status == robot.STATUS_CHARGING:
                counts["charging"] += 1
            elif robot.status == robot.STATUS_COMPLETED:
                counts["task_complete"] += 1
        
        return counts