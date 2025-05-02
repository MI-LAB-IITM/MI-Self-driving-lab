from archemist.core.persistence.models_proxy import ModelProxy
from archemist.core.models.robot_model import RobotModel
from archemist.core.models.robot_op_model import RobotTaskOpModel
from archemist.core.state.robot import FixedRobot
from archemist.core.state.robot_op import RobotOp, RobotTaskOp
from typing import Union

class Asystr3cRobot(FixedRobot):
    def __init__(self, robot_model: Union[RobotModel, ModelProxy]) -> None:
        super().__init__(robot_model)