from archemist.core.state.station import Station
from .state import VialSelectorVialOpenOp, VialSelectorContinueStirringOp, VialSelectorStopStirringOp
from archemist.core.processing.handler import StationOpHandler
from archemist.core.util.enums import OpOutcome
from archemist.core.state.station_op_result import ProcessOpResult
from typing import Tuple, List
from time import sleep
from enum import Enum
from threading import Thread
import rclpy
from rclpy.node import Node
from vial_selector_msg.msg import VialselectorCommands, VialselectorFeedback

current_command = None

class VialSelectorROS2Handler(StationOpHandler):

    def __init__(self, station: Station):
        super().__init__(station)
    
    def initialise(self):     
        self._running = None
        self._is_operation_success = None

        rclpy.init(args=None)        
        self.ros2_node = VialSelectorROS2Node()
        self.spin_node()

        return True
    
    def spin_node(self):
        self._running = True      
        self._spin_thread = Thread(target=self._spin_ros, daemon=True)
        self._spin_thread.start()

    def _spin_ros(self):        
        if self._running:    
            rclpy.spin(self.ros2_node)
        else:
            rclpy.ok()
            self.ros2_node.get_logger().info("Shutting down VialSelectorROS2Handler node")
            rclpy.shutdown()
    
    def execute_op(self):

        current_op = self._station.assigned_op
        if isinstance(current_op, VialSelectorVialOpenOp):
            self.ros2_node.get_logger().info(f"Executing vial selection and opening operation")
            msg = VialselectorCommands(command="selectAndOpenVial", vial_number=current_op.vial_number)            
            self.publish_message(msg)
        
        elif isinstance(current_op, VialSelectorContinueStirringOp):
            self.ros2_node.get_logger().info(f"Executing stirring operation")
            msg = VialselectorCommands(command="continueStirring")            
            self.publish_message(msg)

        elif isinstance(current_op, VialSelectorStopStirringOp):
            self.ros2_node.get_logger().info(f"Executing shutdown operation")
            msg = VialselectorCommands(command="stopStirring")            
            self.publish_message(msg)
        
        else:
            self.ros2_node.get_logger().warn(f"Unknown operation received: {type(current_op).__name__}")        

    def publish_message(self, msg:VialselectorCommands):
        self.ros2_node._is_operation_success = None
        global current_command
        current_command = msg.command
        #for _ in range(10):
        self.ros2_node._vialSelector_pub.publish(msg)
        self.ros2_node.get_logger().info(f"Published Vial Selector {current_command} command")

    def is_op_execution_complete(self) -> bool:
        self._is_operation_success = self.ros2_node._is_operation_success
        return self._is_operation_success is not None

    def get_op_result(self) -> Tuple[OpOutcome, List[ProcessOpResult]]:
        return (OpOutcome.SUCCEEDED, None) if self._is_operation_success else (OpOutcome.FAILED, None)
    
    def shut_down(self):
        if self._running:
            self._running = False  

class VialSelectorROS2Node(Node):
    _is_operation_success = None

    def __init__(self):  
        super().__init__('VialSelectorROS2_handler')
        self._vialSelector_pub = self.create_publisher(VialselectorCommands, "vialSelector_commands", 10)
        self.create_subscription(VialselectorFeedback, "vialSelector_results", self._vial_selector_callback, 10)
        self.get_logger().info("VialSelectorROS2Handler initialized")
    
    def _vial_selector_callback(self, msg: VialselectorFeedback):
        self._is_operation_success = msg.is_operation_success
        if msg.is_operation_success:
            self.get_logger().info(f"{current_command} Operation executed successfully")