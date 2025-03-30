"""import logging
from collections import defaultdict

class TrafficManager:
    def __init__(self, logger=None):
        # Track which lanes are occupied and by which robots
        self.occupied_lanes = {}  # Format: {(from_vertex, to_vertex): robot_id}
        
        # Queue of robots waiting for each lane
        self.lane_queues = defaultdict(list)  # Format: {(from_vertex, to_vertex): [robot_id1, robot_id2, ...]}
        
        # Track robots waiting at vertices
        self.waiting_at_vertex = defaultdict(list)  # Format: {vertex_id: [robot_id1, robot_id2, ...]}
        
        self.logger = logger or logging.getLogger(__name__)
    
    def request_lane_access(self, robot, from_vertex, to_vertex):
        #Check if lane is available and reserve it if it is, otherwise queue the robot
        lane_key = (from_vertex, to_vertex)
        
        if lane_key in self.occupied_lanes:
            # Lane is occupied, add robot to queue
            if robot.id not in self.lane_queues[lane_key]:
                self.lane_queues[lane_key].append(robot.id)
                
                # Add to waiting at vertex list
                if robot.id not in self.waiting_at_vertex[from_vertex]:
                    self.waiting_at_vertex[from_vertex].append(robot.id)
                
                occupying_robot = self.occupied_lanes[lane_key]
                self.logger.info(f"Lane from {from_vertex} to {to_vertex} is occupied by Robot {occupying_robot}. Robot {robot.id} queued.")
            return False
        
        # Lane is free, reserve it
        self.occupied_lanes[lane_key] = robot.id
        
        # Remove from waiting lists if present
        if robot.id in self.lane_queues[lane_key]:
            self.lane_queues[lane_key].remove(robot.id)
        
        if robot.id in self.waiting_at_vertex[from_vertex]:
            self.waiting_at_vertex[from_vertex].remove(robot.id)
            
        self.logger.info(f"Lane from {from_vertex} to {to_vertex} reserved by Robot {robot.id}")
        return True
    
    def release_lane(self, from_vertex, to_vertex):
        #Release a lane reservation and notify next robot in queue if any
        lane_key = (from_vertex, to_vertex)
        if lane_key in self.occupied_lanes:
            robot_id = self.occupied_lanes[lane_key]
            del self.occupied_lanes[lane_key]
            self.logger.info(f"Lane from {from_vertex} to {to_vertex} released by Robot {robot_id}")
            
            # Check if there are robots waiting for this lane
            if self.lane_queues[lane_key]:
                next_robot_id = self.lane_queues[lane_key][0]
                self.logger.info(f"Notifying Robot {next_robot_id} that lane from {from_vertex} to {to_vertex} is now available")
                return True, next_robot_id
            return True, None
        return False, None
    
    def is_lane_occupied(self, from_vertex, to_vertex):
        #Check if a lane is currently occupied
        return (from_vertex, to_vertex) in self.occupied_lanes
    
    def get_occupying_robot(self, from_vertex, to_vertex):
        #Get the ID of the robot occupying a lane
        lane_key = (from_vertex, to_vertex)
        if lane_key in self.occupied_lanes:
            return self.occupied_lanes[lane_key]
        return None
    
    def get_queue_position(self, robot_id, from_vertex, to_vertex):
        #Get the position of a robot in the queue for a lane
        lane_key = (from_vertex, to_vertex)
        if robot_id in self.lane_queues[lane_key]:
            return self.lane_queues[lane_key].index(robot_id) + 1
        return 0
    
    def get_waiting_robots_at_vertex(self, vertex_id):
        #Get list of robots waiting at a vertex
        return self.waiting_at_vertex.get(vertex_id, [])
    
    def get_queue_length(self, from_vertex, to_vertex):
        #Get the number of robots waiting for a lane
        lane_key = (from_vertex, to_vertex)
        return len(self.lane_queues[lane_key])"""