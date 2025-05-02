from transitions import State
from archemist.core.state.lot import Lot
from .state import EZSpinA1SpinCoaterStation, EZSpinA1OpenLidOp, EZSpinA1VacuumONOp, EZSpinA1CloseLidOp, EZSpinA1SpinCoatOp, EZSpinA1VacuumOFFOp, EZSpinA1CheckSpinCoatCompletionOp
from archemist.core.persistence.models_proxy import ModelProxy
from archemist.stations.vial_selector_station.state import VialSelectorVialOpenOp, VialSelectorContinueStirringOp
from archemist.robots.asystr3c_robot.handler import EquipmentStates as EquipmentMap
from archemist.core.state.robot_op import DropBatchOp, RobotTaskOp
from archemist.core.state.station_process import StationProcess, StationProcessModel
from typing import Union, Dict, Any, List
from archemist.core.exceptions.exception import AspirationVolumeBeyondLimitError, DispensingVolumeBeyondCapacityError
import time

# Declaring global variables as custom defined triggers reset the class variables to initial values during transition.
passes_completed = 0
liquid_available_in_dispenser = 0
is_reaspirating = False

class EZSpinA1SpinCoatingProcess(StationProcess):
    def __init__(self, process_model: Union[StationProcessModel, ModelProxy]) -> None:
        super().__init__(process_model)        

        ''' States '''
        self.STATES = [ State(name='init_state'),
            State(name='open_lid_1', on_enter=['open_lid']),
            State(name='place_sample', on_enter=['request_place_substrate']),
            State(name='vacuum_ON', on_enter=['turn_vacuum_ON']),
            State(name='release_sample', on_enter=['request_release_substrate']),
            State(name='close_lid_1', on_enter=['close_lid']),
            State(name='load_pipette_tip', on_enter=['load_pipette_tip']),
            State(name='choose_vial', on_enter=['request_choose_vial']),
            State(name='aspirate_from_vial', on_enter=['request_aspirate_from_vial']),
            State(name='continue_stirring_VialSelector', on_enter=['request_continue_stirring_VialSelector']),
            State(name='standby_to_dispense', on_enter=['request_standby_to_dispense']),
            State(name='check_liquid_adequacy', on_enter=['check_liquid_adequacy']),
            State(name='spin_substrate', on_enter=['spin_substrate']),
            State(name='dispense_liquid', on_enter=['request_dispense_liquid']),
            State(name='stop_spin_coating', on_enter=['check_is_spin_coating_completed']),
            State(name='repeat_passes', on_enter=['request_repeat_pass']),
            State(name='cobot_to_stby_state', on_enter=['request_cobot_to_stby_state']),
            State(name='open_lid_2', on_enter=['open_lid']),
            State(name='hold_sample_for_release', on_enter=['request_hold_substrate_for_release']),            
            State(name='vacuum_OFF', on_enter=['turn_vacuum_OFF']),
            State(name='unload_sample', on_enter=['request_unload_sample']),
            State(name='close_lid_2', on_enter=['close_lid']),
            State(name='final_state')]

        ''' Transitions '''
        self.TRANSITIONS = [
            {'source':'init_state'              ,'dest':'open_lid_1'},
            {'source':'open_lid_1'              ,'dest':'place_sample'                  , 'conditions':'are_req_station_ops_completed'},
            {'source':'place_sample'            ,'dest':'vacuum_ON'                     , 'conditions':'are_req_robot_ops_completed'},
            {'source':'vacuum_ON'               ,'dest':'release_sample'                , 'conditions':'are_req_station_ops_completed'},
            {'source':'release_sample'          ,'dest':'close_lid_1'                   , 'conditions':'are_req_robot_ops_completed'},
            {'source':'close_lid_1'             ,'dest':'load_pipette_tip'              , 'conditions':'are_req_station_ops_completed'},
            {'source':'load_pipette_tip'        ,'dest':'choose_vial'                   , 'conditions':'are_req_robot_ops_completed'},           
            {'source':'choose_vial'             ,'dest':'aspirate_from_vial'            , 'conditions':'are_req_station_ops_completed'},    
            {'source':'aspirate_from_vial'      ,'dest':'continue_stirring_VialSelector', 'conditions':'is_aspiration_successful'},
            {'source':'continue_stirring_VialSelector','dest':'standby_to_dispense'     , 'conditions':'are_req_station_ops_completed'},
            {'source':'standby_to_dispense'     ,'dest':'check_liquid_adequacy'         , 'conditions':'are_req_robot_ops_completed'},
            {'source':'check_liquid_adequacy'   ,'dest':'spin_substrate'                , 'conditions':'is_dispensing_liquid_adequate'},
            {'source':'spin_substrate'          ,'dest':'dispense_liquid'               , 'conditions':'are_req_station_ops_completed'},            
            {'source':'dispense_liquid'         ,'dest':'stop_spin_coating'             , 'conditions':'are_req_robot_ops_completed'},
            {'source':'stop_spin_coating'       ,'dest':'repeat_passes'                 , 'conditions':'are_req_station_ops_completed'},
            {'source':'repeat_passes'           ,'dest':'cobot_to_stby_state'},
            {'source':'cobot_to_stby_state'     ,'dest':'open_lid_2'                    , 'conditions':'are_req_robot_ops_completed'},
            {'source':'open_lid_2'              ,'dest':'hold_sample_for_release'       , 'conditions':'are_req_station_ops_completed'},
            {'source':'hold_sample_for_release' ,'dest':'vacuum_OFF'                    , 'conditions':'are_req_robot_ops_completed'},
            {'source':'vacuum_OFF'              ,'dest':'unload_sample'                 , 'conditions':'are_req_station_ops_completed'},
            {'source':'unload_sample'           ,'dest':'close_lid_2'                   , 'conditions':'are_req_robot_ops_completed'},
            {'source':'close_lid_2'             ,'dest':'final_state'                   , 'conditions':'are_req_station_ops_completed'},
            {'source':'check_liquid_adequacy'   ,'dest': 'choose_vial'                  , 'trigger': 'go_to_choose_vial'},
            {'source':'repeat_passes'           ,'dest': 'check_liquid_adequacy'        , 'trigger': 'go_to_check_liquid_adequacy'},  
            {'source':'repeat_passes'           ,'dest': 'cobot_to_stby_state'          , 'trigger': 'go_to_cobot_to_stby'},
                                 
        ]
        
    @classmethod
    def from_args(cls, lot: Lot,
                  vial_number: int,
                  new_pipette_tip_required: bool,
                  eject_pipette_tip: bool,
                  aspiration_volume: int,
                  dispense_volume_per_pass: int,
                  volume_unit: str,
                  number_of_passes: int,
                  substrate_id: int,
                  pipette_tip_id: int,
                  operations: List[Dict[str, Any]] = None,
                  is_subprocess: bool=False,
                  skip_robot_ops: bool=False,
                  skip_station_ops: bool=False,
                  skip_ext_procs: bool=False
                  ):
        model = StationProcessModel()
        cls._set_model_common_fields(model,
                                     EZSpinA1SpinCoaterStation.__name__,
                                     lot,
                                     operations,
                                     is_subprocess,
                                     skip_robot_ops,
                                     skip_station_ops,
                                     skip_ext_procs)
        model.data["vial_number"] = vial_number
        model.data["new_pipette_tip_required"] = new_pipette_tip_required
        model.data["eject_pipette_tip"] = eject_pipette_tip
        model.data["aspiration_volume"] = aspiration_volume
        model.data["dispense_volume_per_pass"] = dispense_volume_per_pass        
        model.data["volume_unit"] = volume_unit
        model.data["number_of_passes"] = number_of_passes
        model.data["substrate_id"] = substrate_id
        model.data["pipette_tip_id"] = pipette_tip_id        
        model.save()
        return cls(model)

    ''' states callbacks '''

    def open_lid(self):
        station_op = EZSpinA1OpenLidOp.from_args()
        self.request_station_op(station_op)
    
    def request_place_substrate(self):               
        move_to_CleanSubstrateStation_task = self.create_asystr_task(name="move_to_SubstrateStation",
                            tool = "cobot",
                            command = "traverse",
                            substrate_id = self.data["substrate_id"],
                            from_state = EquipmentMap.CleanSubstrateStation_stby.name,                           
                            to_state = EquipmentMap.CleanSubstrateStation_action.name)
        
        grip_substrate_task = self.create_asystr_task(name="grip_substrate",
                            tool = "gripper",
                            command = "grip_substrate")
        
        move_to_SpinCoater_action_task = self.create_asystr_task(name="move_to_SpinCoater_action",
                            tool = "cobot",
                            command = "traverse",
                            from_state = EquipmentMap.CleanSubstrateStation_action.name,
                            to_state = EquipmentMap.SpinCoater_gripper_action.name)
        
        self.request_robot_ops([move_to_CleanSubstrateStation_task,
                                grip_substrate_task,
                                move_to_SpinCoater_action_task])

    def turn_vacuum_ON(self):
        station_op = EZSpinA1VacuumONOp.from_args()
        time.sleep(10)
        self.request_station_op(station_op)

    def request_release_substrate(self):
        release_substrate_task = self.create_asystr_task(name="release_substrate",
                            tool = "gripper",
                            command = "release_substrate")
        
        move_to_SpinCoater_stby_task = self.create_asystr_task(name="move_to_SpinCoater_stby",
                            tool = "cobot",
                            command = "traverse",
                            from_state = EquipmentMap.SpinCoater_gripper_action.name,
                            to_state = EquipmentMap.SpinCoater_gripper_stby.name)
        
        self.request_robot_ops([release_substrate_task,move_to_SpinCoater_stby_task])

    def close_lid(self):
        station_op = EZSpinA1CloseLidOp.from_args()
        self.request_station_op(station_op)

    def load_pipette_tip(self):
        if (self.data["new_pipette_tip_required"] == "True"):
            move_to_tipAction_task = self.create_asystr_task(name="move_to_tipAction",
                            tool = "cobot",
                            command = "traverse",
                            pipette_tip_id= self.data["pipette_tip_id"],
                            from_state = EquipmentMap.SpinCoater_gripper_stby.name,
                            to_state = EquipmentMap.CleanPipetteTipStation_action.name)
            
            attach_tip_task = self.create_asystr_task(name="attach_tip",
                            tool = "linear_actuator",
                            command = "down",
                            pipette_tip_id= self.data["pipette_tip_id"],
                            from_state = EquipmentMap.SpinCoater_gripper_stby.name,
                            to_state = EquipmentMap.CleanPipetteTipStation_action.name,
                            linear_range = 69)
            
            move_pipette_up_task = self.create_asystr_task(name="move_pipette_up",
                            tool = "linear_actuator",
                            command = "up",
                            pipette_tip_id= self.data["pipette_tip_id"],
                            from_state = EquipmentMap.SpinCoater_gripper_stby.name,
                            to_state = EquipmentMap.CleanPipetteTipStation_action.name)
            
            move_to_VialStation_task = self.create_asystr_task(name="move_to_VialStation",
                            tool = "cobot",
                            command = "traverse",
                            from_state = EquipmentMap.CleanPipetteTipStation_action.name,
                            to_state = EquipmentMap.VialStation_hover.name)
            
            self.request_robot_ops([move_to_tipAction_task,attach_tip_task,move_pipette_up_task,move_to_VialStation_task])        
        else:
            move_to_VialStation_task = self.create_asystr_task(name="move_to_VialStation",
                            tool = "cobot",
                            command = "traverse",
                            from_state = EquipmentMap.SpinCoater_gripper_stby.name,
                            to_state = EquipmentMap.VialStation_hover.name)
            
            self.request_robot_ops([move_to_VialStation_task])
    
    def request_choose_vial(self):
        station_op = VialSelectorVialOpenOp.from_args(self.data["vial_number"])
        self.request_station_op(station_op)
    
    def request_aspirate_from_vial(self):
        global is_reaspirating
        if int(self.data["aspiration_volume"]) > 200: # max capacity of rLine dispensing module 5-200 uL
            raise AspirationVolumeBeyondLimitError()
            return False
        if is_reaspirating:
            current_state =  EquipmentMap.SpinCoater_pipette_action.name
        else:
            current_state = EquipmentMap.VialStation_hover.name
        
        # ensure_pipette_raised_task = self.create_asystr_task(name="raise_pipette",
        #                     tool = "linear_actuator",
        #                     command = "up",
        #                     from_state = EquipmentMap.SpinCoater_gripper_stby.name,
        #                     to_state = EquipmentMap.CleanPipetteTipStation_action.name)
            
        move_to_VialStation_action_task = self.create_asystr_task(name="move_to_VialStation",
                        tool = "cobot",
                        command = "traverse",
                        from_state = current_state,
                        to_state = EquipmentMap.VialStation_action.name)
        
        lower_pipette_task = self.create_asystr_task(name="lower_pipette",
                            tool = "linear_actuator",
                            command = "down",
                            from_state = EquipmentMap.SpinCoater_gripper_stby.name,
                            to_state = EquipmentMap.CleanPipetteTipStation_action.name,
                            linear_range = 53)
    
        aspirate_task = self.create_asystr_task(name="blowout_and_aspirate",
                                            tool="pipette",
                                            command = "aspirate",
                                            aspiration_volume=self.data["aspiration_volume"])
        
        raise_pipette_task = self.create_asystr_task(name="raise_pipette",
                            tool = "linear_actuator",
                            command = "up",
                            from_state = EquipmentMap.SpinCoater_gripper_stby.name,
                            to_state = EquipmentMap.CleanPipetteTipStation_action.name)
        
        move_to_VialStation_stby_task = self.create_asystr_task(name="clear_VialStation",
                        tool = "cobot",
                        command = "traverse",
                        from_state = EquipmentMap.VialStation_action.name,
                        to_state = EquipmentMap.VialStation_hover.name)
    
        self.request_robot_ops([move_to_VialStation_action_task, lower_pipette_task, aspirate_task, raise_pipette_task, move_to_VialStation_stby_task])
                
        is_reaspirating = False

    def is_aspiration_successful(self):        
        if self.are_req_robot_ops_completed():
            global liquid_available_in_dispenser
            liquid_available_in_dispenser = int(self.data["aspiration_volume"])        
            return True
        return False

    def request_continue_stirring_VialSelector(self):
        station_op = VialSelectorContinueStirringOp.from_args()
        self.request_station_op(station_op)

    def request_standby_to_dispense(self):
        move_to_SpinCoater_dispense_position_task = self.create_asystr_task(name="Move_to_dispense_position",
                                                                       tool = "cobot",
                                                                       command = "traverse",
                                                                       from_state=EquipmentMap.VialStation_hover.name,
                                                                       to_state=EquipmentMap.SpinCoater_pipette_action.name)
        
        lower_pipette_task = lower_pipette_task = self.create_asystr_task(name="lower_pipette",
                            tool = "linear_actuator",
                            command = "down",
                            from_state = EquipmentMap.SpinCoater_gripper_stby.name,
                            to_state = EquipmentMap.CleanPipetteTipStation_action.name,
                            linear_range = 70)
        
        self.request_robot_ops([move_to_SpinCoater_dispense_position_task, lower_pipette_task])

    def is_dispensing_liquid_adequate(self):
        global liquid_available_in_dispenser
        if int(self.data["dispense_volume_per_pass"]) > liquid_available_in_dispenser:            
            return False
        else:
            return True
    
    def check_liquid_adequacy(self):
        if int(self.data["dispense_volume_per_pass"]) > 200: # max capacity of rLine dispensing module 5-200 uL
            raise DispensingVolumeBeyondCapacityError()
            return False        
        if self.is_dispensing_liquid_adequate():
            return True
        else:
            global is_reaspirating
            is_reaspirating = True
            self.trigger('go_to_choose_vial')        

    def spin_substrate(self):
        parameters = dict(self.operation_specs_map["spinCoating_op"].parameters)
        station_op = EZSpinA1SpinCoatOp.from_args(coating_rpm = parameters["coating_rpm"], 
                                                coating_duration_in_seconds = parameters["coating_duration_in_seconds"])
        self.request_station_op(station_op)        
            
    def request_dispense_liquid(self): 
        dispense_liquid_task = self.create_asystr_task(name="dispense_liquid",
                                                       tool="pipette",
                                                       command="dispense",
                                                       dispense_volume_per_pass=int(self.data["dispense_volume_per_pass"]))
        self.request_robot_ops([dispense_liquid_task])
        global liquid_available_in_dispenser
        liquid_available_in_dispenser -= int(self.data["dispense_volume_per_pass"])
            
    def check_is_spin_coating_completed(self):
        station_op = EZSpinA1CheckSpinCoatCompletionOp.from_args()
        self.request_station_op(station_op)
        global passes_completed
        passes_completed += 1

    def request_repeat_pass(self):
        global passes_completed
        print("Pass requested :",int(self.data["number_of_passes"]))
        print("Pass completed :", int(passes_completed))
        if not (int(self.data["number_of_passes"]) == int(passes_completed)):
            self.trigger('go_to_check_liquid_adequacy')
        else:
            passes_completed = 0
            self.trigger('go_to_cobot_to_stby')
    
    def request_cobot_to_stby_state(self):

        if self.data["eject_pipette_tip"] == "True":
            move_to_TipDisposalBin_task = self.create_asystr_task(name="move_to_TipDisposalBin",
                                                            tool="cobot",
                                                            command="traverse",
                                                            from_state=EquipmentMap.SpinCoater_pipette_action.name,
                                                            to_state=EquipmentMap.PipetteTipDisposalBin_hover.name)
            
            eject_tip_task = self.create_asystr_task(name="eject_tip",
                                                    tool="pipette",
                                                    command="eject")
            
            move_to_SpinCoater_gripper_stby_task = self.create_asystr_task(name="move_to_SpinCoater_gripper_stby",
                                                            tool="cobot",
                                                            command="traverse",
                                                            from_state=EquipmentMap.PipetteTipDisposalBin_hover.name,
                                                            to_state=EquipmentMap.SpinCoater_gripper_stby.name)
            
            self.request_robot_ops([move_to_TipDisposalBin_task, eject_tip_task, move_to_SpinCoater_gripper_stby_task])
        else:
            clear_to_open_lid_task = self.create_asystr_task(name="clear_space_to_open_lid",
                                                            tool="cobot",
                                                            command="traverse",
                                                            from_state=EquipmentMap.SpinCoater_pipette_action.name,
                                                            to_state=EquipmentMap.SpinCoater_gripper_stby.name)
            self.request_robot_ops([clear_to_open_lid_task])

    def request_hold_substrate_for_release(self):
        move_to_grip_substrate_task = self.create_asystr_task(name="move_to_grip_substrate",
                                                         tool="cobot",
                                                         command="traverse",
                                                         from_state=EquipmentMap.SpinCoater_gripper_stby.name,
                                                         to_state=EquipmentMap.SpinCoater_gripper_action.name)
        
        hold_substrate_task=self.create_asystr_task(name="hold_substrate",
                                                    tool="gripper",
                                                    command="grip_substrate")        
        self.request_robot_ops([move_to_grip_substrate_task, hold_substrate_task])

    def turn_vacuum_OFF(self):
        station_op = EZSpinA1VacuumOFFOp.from_args()
        time.sleep(10)
        self.request_station_op(station_op)
    
    def request_unload_sample(self):
        move_substrate_to_StorageStation_task = self.create_asystr_task(name="move_substrate_to_StorageStation",
                                                        tool="cobot",
                                                        command="traverse",
                                                        from_state=EquipmentMap.SpinCoater_gripper_action.name,
                                                        to_state=EquipmentMap.CoatedSubstrateStation_action.name)
        
        release_substrate_task = self.create_asystr_task(name="release_substrate",
                                                    tool="gripper",
                                                    command="release_substrate")
        
        move_to_SubstrateStation_stby_task = self.create_asystr_task(name="move_to_SubstrateStation_stby",
                                                        tool="cobot",
                                                        command="traverse",
                                                        from_state=EquipmentMap.CoatedSubstrateStation_action.name,
                                                        to_state=EquipmentMap.CleanSubstrateStation_stby.name)
        
        self.request_robot_ops([move_substrate_to_StorageStation_task, release_substrate_task, move_to_SubstrateStation_stby_task])
    
    def create_asystr_task(self,
                            name = "undefined", 
                            tool = "cobot",
                            command = "do_nothing",
                            aspiration_volume = 0,
                            dispense_volume_per_pass = 0,
                            substrate_id = 0,
                            pipette_tip_id = 0,                           
                            from_state = "invalid",
                            to_state = "invalid",
                            linear_range = 0):
        params_dict ={}
        params_dict["tool"] = tool,
        params_dict["command"] = command,
        params_dict["aspiration_volume"] = aspiration_volume,
        params_dict["dispense_volume_per_pass"] = dispense_volume_per_pass,
        params_dict["substrate_id"] = substrate_id,
        params_dict["pipette_tip_id"] = pipette_tip_id,
        params_dict["from_state"] = from_state,
        params_dict["to_state"] = to_state,
        params_dict["linear_range"] = linear_range

        robot_task = RobotTaskOp.from_args(name=name,
                                           target_robot = "Asystr3cRobot",
                                           params = params_dict)
        return robot_task