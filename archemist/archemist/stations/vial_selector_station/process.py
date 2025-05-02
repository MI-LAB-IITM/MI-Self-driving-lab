from transitions import State
from archemist.core.state.lot import Lot
from .state import VialSelectorStation, VialSelectorVialOpenOp, VialSelectorContinueStirringOp, VialSelectorStopStirringOp
from archemist.core.persistence.models_proxy import ModelProxy
from archemist.core.state.robot_op import DropBatchOp, RobotTaskOp
from archemist.core.state.station_op import StationOp
from archemist.core.state.station_process import StationProcess, StationProcessModel
from typing import Union, Dict, Any, List
from datetime import datetime, timedelta


class VialSelectionProcess(StationProcess):
    def __init__(self, process_model: Union[StationProcessModel, ModelProxy]) -> None:
        super().__init__(process_model)

        ''' States '''
        self.STATES = [ State(name='stirring'),
            State(name='choose_vial_and_open', on_enter=['choose_vial_and_open']),
            State(name='aspirate_liquid'     , on_enter=['request_aspirate_liquid']),
            State(name='stirring'            , on_enter=['close_and_continue_stirring'])]

        ''' Transitions '''
        self.TRANSITIONS = [
            {'source':'stirring'                ,'dest':'choose_vial_and_open'},
            {'source':'choose_vial_and_open'    ,'dest':'aspirate_liquid'           , 'conditions':'are_req_station_ops_completed'},
            {'source':'aspirate_liquid'         ,'dest':'stirring'                  , 'conditions':'are_req_robot_ops_completed'},            
        ]

    @classmethod
    def from_args(cls, lot: Lot,
                  vial_number: int=1,
                  aspiration_volume: int=20,
                  operations: List[Dict[str, Any]] = None,
                  is_subprocess: bool=False,
                  skip_robot_ops: bool=False,
                  skip_station_ops: bool=False,
                  skip_ext_procs: bool=False
                  ):
        model = StationProcessModel()
        cls._set_model_common_fields(model,
                                     VialSelectorStation.__name__,
                                     lot,
                                     operations,
                                     is_subprocess,
                                     skip_robot_ops,
                                     skip_station_ops,
                                     skip_ext_procs)
        model.data["vial_number"] = vial_number
        model.data["aspiration_volume"] = aspiration_volume
        model.save()
        return cls(model)

    ''' states callbacks '''
    def choose_vial_and_open(self):
        station_op = VialSelectorVialOpenOp.from_args(vial_number = self.data["vial_number"])
        self.request_station_op(station_op)

    def request_aspirate_liquid(self):
        params_dict ={}
        params_dict["aspiration_volume"] = self.data["aspiration_volume"]
        robot_task = RobotTaskOp.from_args(name="VialSelectorAspirateLiquid",
                                           target_robot = "Asystr3cRobot",
                                           params = params_dict)
        self.request_robot_ops([robot_task])

    def close_and_continue_stirring(self):
        station_op = VialSelectorContinueStirring.from_args()
        self.request_station_op(station_op)
    
    def stop_stirring(self):
        station_op = VialSelectorStopStirring.from_args()
        self.request_station_op(station_op)

    


