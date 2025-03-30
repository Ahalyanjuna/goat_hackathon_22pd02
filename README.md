# goat_hackathon_22pd02
 
Features
* More than one robot cannot occupy the same lane and vertex at a time.
* BFS Algorithm is used to find paths from source to destination.
* When a required lane or vertex is occupied by another robot the, the robot waits in queue till the lane or vertex is free.
* When a robot is at charging station, we can enable charging by using the charge robot option in the GUI.
* As given in the problem statement, a robot can be spawned, assigned destination and charged by using the features in the GUI.
* The current status of the robots can be viewed in the GUI itself.

Classes
* NavigationGraph - Physical layout of vertices and lanes is mapped from the json file.
* Robot - To represent state and behaviour of each robot.
* FleetManager - To assign navigation tasks.
* TrafficManager - Traffic management (reservation for lanes and vertices).

How to use the GUI ?
* Click on a vertex to spawn a robot there.
* Click on a robot and then click on the destination vertex to assign its destination.
* If vertex is a charging station, clicking on 'charge robot' allows the robot to get charged.
* The number of robots in different states can be kept track of using the side panel. 
