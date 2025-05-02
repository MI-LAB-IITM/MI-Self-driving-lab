from .model import EZSpinA1SpinCoaterJobStatus, EZSpinA1SpinCoaterStationModel, EZSpinA1SpinCoaterOpModel
from archemist.core.persistence.models_proxy import ModelProxy, DictProxy
from archemist.core.models.station_op_model import StationOpModel
from archemist.core.state.station import Station
from archemist.core.state.lot import Lot
from archemist.core.state.station_op import StationOp
from archemist.core.state.station_op_result import StationOpResult
from typing import List, Dict, Type, Union
from archemist.core.util.enums import OpOutcome


''' ==== Station Description ==== '''
class EZSpinA1SpinCoaterStation(Station):
    def __init__(self, station_model: Union[EZSpinA1SpinCoaterStationModel,ModelProxy]) -> None:
        super().__init__(station_model)

    @classmethod
    def from_dict(cls, station_dict: Dict):
        model = EZSpinA1SpinCoaterStationModel()
        cls._set_model_common_fields(model, station_dict)
        model.save()
        return cls(model)


''' ==== Station Operation Descriptors ==== '''
class EZSpinA1OpenLidOp(StationOp):
    def __init__(self, station_op_model: Union[StationOpModel,ModelProxy]) -> None:
        super().__init__(station_op_model)

    @classmethod
    def from_args(cls):
        model = StationOpModel()
        cls._set_model_common_fields(model, associated_station=EZSpinA1SpinCoaterStation.__name__)
        model.save()
        return cls(model)
    
class EZSpinA1VacuumONOp(StationOp):
    def __init__(self, station_op_model: Union[StationOpModel,ModelProxy]) -> None:
        super().__init__(station_op_model)

    @classmethod
    def from_args(cls):
        model = StationOpModel()
        cls._set_model_common_fields(model, associated_station=EZSpinA1SpinCoaterStation.__name__)
        model.save()
        return cls(model)
    
class EZSpinA1VacuumOFFOp(StationOp):
    def __init__(self, station_op_model: Union[StationOpModel,ModelProxy]) -> None:
        super().__init__(station_op_model)

    @classmethod
    def from_args(cls):
        model = StationOpModel()
        cls._set_model_common_fields(model, associated_station=EZSpinA1SpinCoaterStation.__name__)
        model.save()
        return cls(model)

class EZSpinA1CloseLidOp(StationOp):
    def __init__(self, station_op_model: Union[StationOpModel,ModelProxy]) -> None:
        super().__init__(station_op_model)

    @classmethod
    def from_args(cls):
        model = StationOpModel()
        cls._set_model_common_fields(model, associated_station=EZSpinA1SpinCoaterStation.__name__)
        model.save()
        return cls(model)

class EZSpinA1SpinCoatOp(StationOp):
    def __init__(self, station_op_model: Union[EZSpinA1SpinCoaterOpModel,ModelProxy]) -> None:
        super().__init__(station_op_model)

    @classmethod
    def from_args(cls,
                  coating_rpm : int,
                  coating_duration_in_seconds : int,
                  ):
        model = EZSpinA1SpinCoaterOpModel()
        cls._set_model_common_fields(model, associated_station=EZSpinA1SpinCoaterStation.__name__)
        model.coating_rpm = coating_rpm
        model.coating_duration_in_seconds = coating_duration_in_seconds
        model.save()
        return cls(model)
    
    @property
    def coating_rpm(self):
        return self._model_proxy.coating_rpm
    
    @property
    def coating_duration_in_seconds(self):
        return self._model_proxy.coating_duration_in_seconds

class EZSpinA1CheckSpinCoatCompletionOp(StationOp):
    def __init__(self, station_op_model: Union[StationOpModel,ModelProxy]) -> None:
        super().__init__(station_op_model)

    @classmethod
    def from_args(cls):
        model = StationOpModel()
        cls._set_model_common_fields(model, associated_station=EZSpinA1SpinCoaterStation.__name__)
        model.save()
        return cls(model)