import json

class NavigationGraph:
    def __init__(self, json_file_path):
        self.vertices = []
        self.lanes = []
        self.vertex_map = {}  # Maps vertex index to its data
        self.load_from_json(json_file_path)
        
    def load_from_json(self, json_file_path):
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                
            # Extract the first level found
            level_key = list(data["levels"].keys())[0]
            level_data = data["levels"][level_key]
            
            # Process vertices
            self.vertices = level_data["vertices"]
            
            # Create a mapping for easy lookup
            for i, vertex in enumerate(self.vertices):
                self.vertex_map[i] = {
                    "coords": (vertex[0], vertex[1]),
                    "name": vertex[2].get("name", f"V{i}"),
                    "is_charger": vertex[2].get("is_charger", False)
                }
            
            # Process lanes
            self.lanes = level_data["lanes"]
            
        except Exception as e:
            print(f"Error loading nav_graph: {e}")
            raise
    
    def get_vertex_coords(self, vertex_index):
        if vertex_index in self.vertex_map:
            return self.vertex_map[vertex_index]["coords"]
        return None
    
    def get_vertex_name(self, vertex_index):
        if vertex_index in self.vertex_map:
            return self.vertex_map[vertex_index]["name"] or f"V{vertex_index}"
        return f"V{vertex_index}"
    
    def is_charger(self, vertex_index):
        if vertex_index in self.vertex_map:
            return self.vertex_map[vertex_index]["is_charger"]
        return False
    
    def get_connected_vertices(self, vertex_index):
        """Returns a list of vertex indices that can be reached from the given vertex"""
        connected = []
        for lane in self.lanes:
            # Check for both directions
            if lane[0] == vertex_index:
                connected.append(lane[1])
            #Uncomment if bidirectional movement is allowed
            if lane[1] == vertex_index:
                connected.append(lane[0])
        
        #self.logger.info(f"Vertex {vertex_index} is connected to: {connected}")
        return connected