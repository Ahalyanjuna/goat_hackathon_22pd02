

import logging
from collections import defaultdict

class TrafficManager:
    def __init__(self, logger=None):
        # Track which lanes are occupied and by which robots
        self.occupied_lanes = {}  # Format: {(from_vertex, to_vertex): robot_id}
        
        # Queue of robots waiting for each lane
        self.lane_queues = defaultdict(list)  # Format: {(from_vertex, to_vertex): [robot_id1, robot_id2, ...]}
        
        # Track robots waiting at vertices
        self.waiting_at_vertex = defaultdict(list)  # Format: {vertex_id: [robot_id1, robot_id2, ...]}
        
        # Track which robots are occupying which vertices
        self.occupied_vertices = {}  # Format: {vertex_id: robot_id}
        
        # Queue of robots waiting for each vertex
        self.vertex_queues = defaultdict(list)  # Format: {vertex_id: [robot_id1, robot_id2, ...]}
        
        self.logger = logger or logging.getLogger(__name__)
    
    def request_lane_access(self, robot, from_vertex, to_vertex):
        """
        Check if lane is available and the destination vertex is free,
        and reserve them if they are, otherwise queue the robot
        """
        lane_key = (from_vertex, to_vertex)
        
        # First check if the destination vertex is occupied by another robot
        vertex_occupied = False
        if to_vertex in self.occupied_vertices and self.occupied_vertices[to_vertex] != robot.id:
            # Vertex is occupied by another robot
            vertex_occupied = True
            if robot.id not in self.vertex_queues[to_vertex]:
                self.vertex_queues[to_vertex].append(robot.id)
                self.logger.info(f"Vertex {to_vertex} is occupied by Robot {self.occupied_vertices[to_vertex]}. Robot {robot.id} queued.")
        
        # Then check if the lane is occupied
        lane_occupied = False
        if lane_key in self.occupied_lanes:
            # Lane is occupied, add robot to queue
            lane_occupied = True
            if robot.id not in self.lane_queues[lane_key]:
                self.lane_queues[lane_key].append(robot.id)
                
                # Add to waiting at vertex list
                if robot.id not in self.waiting_at_vertex[from_vertex]:
                    self.waiting_at_vertex[from_vertex].append(robot.id)
                
                occupying_robot = self.occupied_lanes[lane_key]
                self.logger.info(f"Lane from {from_vertex} to {to_vertex} is occupied by Robot {occupying_robot}. Robot {robot.id} queued.")
        
        # If either lane or destination vertex is occupied, robot must wait
        if lane_occupied or vertex_occupied:
            return False
        
        # Both lane and vertex are free, reserve them
        self.occupied_lanes[lane_key] = robot.id
        
        # Remove from waiting lists if present
        if robot.id in self.lane_queues[lane_key]:
            self.lane_queues[lane_key].remove(robot.id)
        
        if robot.id in self.waiting_at_vertex[from_vertex]:
            self.waiting_at_vertex[from_vertex].remove(robot.id)
            
        self.logger.info(f"Lane from {from_vertex} to {to_vertex} reserved by Robot {robot.id}")
        return True
    
    def release_lane(self, from_vertex, to_vertex):
        """Release a lane reservation and notify next robot in queue if any"""
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
    
    def occupy_vertex(self, robot_id, vertex_id):
        """Mark a vertex as occupied by a robot"""
        # If the vertex was already occupied by this robot, no change
        if vertex_id in self.occupied_vertices and self.occupied_vertices[vertex_id] == robot_id:
            return
            
        # Otherwise, mark it as occupied and log
        self.occupied_vertices[vertex_id] = robot_id
        self.logger.info(f"Vertex {vertex_id} occupied by Robot {robot_id}")
        
    def release_vertex(self, vertex_id):
        """Release a vertex and notify waiting robots if any"""
        if vertex_id in self.occupied_vertices:
            robot_id = self.occupied_vertices[vertex_id]
            del self.occupied_vertices[vertex_id]
            self.logger.info(f"Vertex {vertex_id} released by Robot {robot_id}")
            
            # Check if there are robots waiting for this vertex
            if self.vertex_queues[vertex_id]:
                next_robot_id = self.vertex_queues[vertex_id][0]
                self.logger.info(f"Notifying Robot {next_robot_id} that vertex {vertex_id} is now available")
                return True, next_robot_id
            return True, None
        return False, None
    
    def is_lane_occupied(self, from_vertex, to_vertex):
        """Check if a lane is currently occupied"""
        return (from_vertex, to_vertex) in self.occupied_lanes
    
    def is_vertex_occupied(self, vertex_id, robot_id=None):
        """
        Check if a vertex is currently occupied by any robot other than robot_id
        If robot_id is None, check if occupied by any robot
        """
        if vertex_id not in self.occupied_vertices:
            return False
            
        if robot_id is None:
            return True
            
        # Check if occupied by a different robot
        return self.occupied_vertices[vertex_id] != robot_id
    
    def get_occupying_robot(self, from_vertex, to_vertex):
        """Get the ID of the robot occupying a lane"""
        lane_key = (from_vertex, to_vertex)
        if lane_key in self.occupied_lanes:
            return self.occupied_lanes[lane_key]
        return None
    
    def get_vertex_occupying_robot(self, vertex_id):
        """Get the ID of the robot occupying a vertex"""
        if vertex_id in self.occupied_vertices:
            return self.occupied_vertices[vertex_id]
        return None
    
    def get_queue_position(self, robot_id, from_vertex, to_vertex):
        """Get the position of a robot in the queue for a lane"""
        lane_key = (from_vertex, to_vertex)
        if robot_id in self.lane_queues[lane_key]:
            return self.lane_queues[lane_key].index(robot_id) + 1
        return 0
    
    def get_vertex_queue_position(self, robot_id, vertex_id):
        """Get the position of a robot in the queue for a vertex"""
        if robot_id in self.vertex_queues[vertex_id]:
            return self.vertex_queues[vertex_id].index(robot_id) + 1
        return 0
    
    def get_waiting_robots_at_vertex(self, vertex_id):
        """Get list of robots waiting at a vertex"""
        return self.waiting_at_vertex.get(vertex_id, [])
    
    def get_queue_length(self, from_vertex, to_vertex):
        """Get the number of robots waiting for a lane"""
        lane_key = (from_vertex, to_vertex)
        return len(self.lane_queues[lane_key])
    
    def get_vertex_queue_length(self, vertex_id):
        """Get the number of robots waiting for a vertex"""
        return len(self.vertex_queues[vertex_id])