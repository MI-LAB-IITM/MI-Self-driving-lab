from archemist.core.state.robot import Robot
from archemist.core.processing.handler import RobotOpHandler
from archemist.core.util.enums import OpOutcome
from enum import Enum, auto
from threading import Thread
import rclpy
from rclpy.node import Node
from asystr3c_msg.msg import AsystrTask, AsystrFeedback

current_command = None

#defining the equipment map, these are the various positions within which the cobot can traverse.
class EquipmentStates(Enum):

    cobot_home = auto()

    SpinCoater_gripper_stby = auto()
    SpinCoater_gripper_hover = auto ()
    SpinCoater_gripper_action = auto()
    
    SpinCoater_pipette_stby = auto()
    SpinCoater_pipette_hover = auto ()
    SpinCoater_pipette_action = auto()

    CleanSubstrateStation_stby = auto()
    CleanSubstrateStation_hover = auto()
    CleanSubstrateStation_action = auto()

    CoatedSubstrateStation_stby = auto()
    CoatedSubstrateStation_hover = auto()
    CoatedSubstrateStation_action = auto()

    VialStation_stby = auto()
    VialStation_hover = auto()
    VialStation_action = auto()

    CleanPipetteTipStation_stby = auto()
    CleanPipetteTipStation_hover = auto()
    CleanPipetteTipStation_action = auto()

    PipetteTipDisposalBin_stby = auto()
    PipetteTipDisposalBin_hover = auto()

class Asystr3cROSHandler(RobotOpHandler):
    def __init__(self, robot: Robot):
        super().__init__(robot)

    def initialise(self):     
        self._running = None
        self._is_operation_success = None
        self.current_op = None

        rclpy.init(args=None)        
        self.ros2_node = Asystr3cROS2Node()
        self.spin_node()

        return True
    
    def spin_node(self):
        self._running = True      
        self._spin_thread = Thread(target=self._spin_ros, daemon=True)
        self._spin_thread.start()

    def _spin_ros(self):        
        while self._running:    
            rclpy.spin_once(node = self.ros2_node, timeout_sec = 0.1 )        
        rclpy.ok()
        self.ros2_node.get_logger().info("Shutting down Asystr3cROSHandler node")
        rclpy.shutdown()
    
    def execute_op(self):
        self.current_op = self._robot.assigned_op

        if self.current_op.target_robot == "Asystr3cRobot":
            task_msg = AsystrTask()
            # value of params["tool"] is returned as a BaseList (i.e ["gripper"]) by mongo DB.
            # hence using [0] at the end of each param to get only the value.
            task_msg.tool = str(self.current_op.params["tool"][0])
            task_msg.command = str(self.current_op.params["command"][0])
            task_msg.aspiration_volume = int(self.current_op.params["aspiration_volume"][0])
            task_msg.dispense_volume_per_pass = int(self.current_op.params["dispense_volume_per_pass"][0])
            task_msg.substrate_id = int(self.current_op.params["substrate_id"][0])
            task_msg.pipette_tip_id = int(self.current_op.params["pipette_tip_id"][0])
            task_msg.from_state = str(self.current_op.params["from_state"][0])
            task_msg.to_state = str(self.current_op.params["to_state"][0])
            task_msg.linear_range = int(self.current_op.params["linear_range"])
            self.ros2_node.get_logger().info(f"Executing  Asystr_3c {self.current_op.name} operation")
            self.publish_message(task_msg)
        else:
            self.ros2_node.get_logger().warn(f"Unknown operation received: {type(self.current_op).__name__}")

    def publish_message(self, msg):
        self.ros2_node._is_operation_success = None
        global current_command
        current_command = self.current_op.name
        self.ros2_node.asystr_pub.publish(msg)
        self.ros2_node.get_logger().info(f"Published Asystr3c {current_command} command") 

    def is_op_execution_complete(self) -> bool:
        self._is_operation_success = self.ros2_node._is_operation_success
        return self._is_operation_success is not None
    
    def get_op_result(self) -> OpOutcome:
        return OpOutcome.SUCCEEDED if self._is_operation_success else OpOutcome.FAILED

    def shut_down(self):
        if self._running:
            self._running = False

class Asystr3cROS2Node(Node):
    _is_operation_success = None

    def __init__(self):  
        super().__init__('Asystr3cROS2_handler')
        self.asystr_pub = self.create_publisher(AsystrTask, "asystr_commands", 10)
        self.create_subscription(AsystrFeedback, "asystr_results", self._asystr_callback, 10)
        self.get_logger().info("Asystr3cROS2Handler initialized")
    
    def _asystr_callback(self, msg: AsystrFeedback):
        self._is_operation_success = msg.is_operation_success
        if msg.is_operation_success:
            self.get_logger().info(f"{current_command} Operation executed successfully")