from archemist.core.state.station import Station
from .state import (
    EZSpinA1VacuumONOp, EZSpinA1VacuumOFFOp, EZSpinA1OpenLidOp,
    EZSpinA1CloseLidOp, EZSpinA1SpinCoatOp, EZSpinA1CheckSpinCoatCompletionOp
)
from archemist.core.processing.handler import StationOpHandler
from archemist.core.util.enums import OpOutcome
from archemist.core.state.station_op_result import ProcessOpResult
from typing import Tuple, List
from enum import Enum
from threading import Thread
import rclpy
from rclpy.node import Node
from ezspin_msg.msg import Apexspincoatercommands, Apexspincoaterfeedback

current_command = None

class EZSpinA1_Commands(Enum):
    VACUUM_ON = 1
    SPIN_COAT = 2
    STOP = 3
    VACUUM_OFF = 4
    LID_OPEN = 5
    LID_CLOSE = 6
    CHECK_IS_COATING_COMPLETE = 7

class EZSpinA1_Feedback_Status(Enum):
    VACUUM_SET_ON = 1
    VACUUM_SET_OFF = 2
    SPIN_COAT_COMPLETE = 3
    SPIN_COAT_COMPLETE_WITH_ERROR = 4
    LID_OPEN_SUCCESS = 5
    LID_OPEN_FAIL = 6
    LID_CLOSE_SUCCESS = 7
    LID_CLOSE_FAIL = 8
    ERROR = 9

class EZSpinA1SpinCoaterROS2Handler(StationOpHandler):
    def __init__(self, station: Station):
        super().__init__(station)

    def initialise(self):     
        self._running = None
        self._is_operation_success = None

        rclpy.init(args=None)        
        self.ros2_node = EZSpinA1SpinCoaterROS2Node()
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
            self.ros2_node.get_logger().info("Shutting down EZSpinA1SpinCoaterROS2Handler node")
            rclpy.shutdown()
    
    def execute_op(self):
        current_op = self._station.assigned_op
        
        if isinstance(current_op, EZSpinA1SpinCoatOp):
            self.ros2_node.get_logger().info(f"Executing {EZSpinA1_Commands.SPIN_COAT.name} operation")
            msg = Apexspincoatercommands(command=EZSpinA1_Commands.SPIN_COAT.value, rpm=current_op.coating_rpm, duration_in_seconds=current_op.coating_duration_in_seconds)            
            self.publish_message(msg)

        elif isinstance(current_op, EZSpinA1VacuumONOp):
            self.ros2_node.get_logger().info(f"Executing {EZSpinA1_Commands.VACUUM_ON.name} operation")
            msg = Apexspincoatercommands(command=EZSpinA1_Commands.VACUUM_ON.value)
            self.publish_message(msg)

        elif isinstance(current_op, EZSpinA1VacuumOFFOp):
            self.ros2_node.get_logger().info(f"Executing {EZSpinA1_Commands.VACUUM_OFF.name} operation")
            msg = Apexspincoatercommands(command=EZSpinA1_Commands.VACUUM_OFF.value)
            self.publish_message(msg)

        elif isinstance(current_op, EZSpinA1OpenLidOp):
            self.ros2_node.get_logger().info(f"Executing {EZSpinA1_Commands.LID_OPEN.name} operation")
            msg = Apexspincoatercommands(command=EZSpinA1_Commands.LID_OPEN.value)
            self.publish_message(msg)

        elif isinstance(current_op, EZSpinA1CloseLidOp):
            self.ros2_node.get_logger().info(f"Executing {EZSpinA1_Commands.LID_CLOSE.name} operation")
            msg = Apexspincoatercommands(command=EZSpinA1_Commands.LID_CLOSE.value)
            self.publish_message(msg)
        
        elif isinstance(current_op, EZSpinA1CheckSpinCoatCompletionOp):
            self.ros2_node.get_logger().info(f"Executing {EZSpinA1_Commands.CHECK_IS_COATING_COMPLETE.name} operation")
            msg = Apexspincoatercommands(command=EZSpinA1_Commands.CHECK_IS_COATING_COMPLETE.value)
            self.publish_message(msg)
            
        else:
            self.ros2_node.get_logger().warn(f"Unknown operation received: {type(current_op).__name__}")

    def publish_message(self, msg:Apexspincoatercommands):
        self.ros2_node._is_operation_success = None
        global current_command
        current_command = EZSpinA1_Commands(msg.command).name
        #for _ in range(10):
        self.ros2_node._ezSpinA1_pub.publish(msg)
        self.ros2_node.get_logger().info(f"Published EZSpinA1 {EZSpinA1_Commands(msg.command).name} command")                
                
    def is_op_execution_complete(self) -> bool:
        self._is_operation_success = self.ros2_node._is_operation_success
        return self._is_operation_success is not None
    
    def get_op_result(self) -> Tuple[OpOutcome, List[ProcessOpResult]]:
        return (OpOutcome.SUCCEEDED, None) if self._is_operation_success else (OpOutcome.FAILED, None)
    
    def shut_down(self):#ToBeCoded
        if self._running:
            self._running = False            

class EZSpinA1SpinCoaterROS2Node(Node):
    _is_operation_success = None

    def __init__(self):  
        super().__init__('EZSpinA1SpinCoaterROS2_handler')
        self._ezSpinA1_pub = self.create_publisher(Apexspincoatercommands, "ezspin_commands", 10)
        self.create_subscription(Apexspincoaterfeedback, "ezspin_results", self._spin_coater_callback, 10)
        self.get_logger().info("EZSpinA1SpinCoaterROS2Handler initialized")
    
    def _spin_coater_callback(self, msg: Apexspincoaterfeedback):
        self._is_operation_success = msg.is_operation_success
        if msg.is_operation_success:
            self.get_logger().info(f"{current_command} Operation executed successfully")
