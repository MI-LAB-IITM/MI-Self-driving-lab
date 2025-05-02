from .model import VialSelectorStationJobStatus, VialSelectorStationModel, VialSelectorStationOpModel
from archemist.core.persistence.models_proxy import ModelProxy, DictProxy
from archemist.core.models.station_op_model import StationOpModel
from archemist.core.state.station import Station
from archemist.core.state.lot import Lot
from archemist.core.state.station_op import StationOp
from archemist.core.state.station_op_result import StationOpResult
from typing import List, Dict, Type, Union
from archemist.core.util.enums import OpOutcome


''' ==== Station Description ==== '''
class VialSelectorStation(Station):
    def __init__(self, station_model: Union[VialSelectorStationModel,ModelProxy]) -> None:
        super().__init__(station_model)

    @classmethod
    def from_dict(cls, station_dict: Dict):
        model = VialSelectorStationModel()
        cls._set_model_common_fields(model, station_dict)
        model.save()
        return cls(model)

''' ==== Station Operation Descriptors ==== '''
class VialSelectorVialOpenOp(StationOp):
    def __init__(self, station_op_model: Union[VialSelectorStationOpModel,ModelProxy]) -> None:
        super().__init__(station_op_model)

    @classmethod
    def from_args(cls, vial_number):
        model = VialSelectorStationOpModel()
        cls._set_model_common_fields(model, associated_station=VialSelectorStation.__name__)
        model.vial_number = vial_number
        model.save()
        return cls(model)

    @property
    def vial_number(self):
        return self._model_proxy.vial_number

class VialSelectorContinueStirringOp(StationOp):
    def __init__(self, station_op_model: Union[StationOpModel,ModelProxy]) -> None:
            super().__init__(station_op_model)

    @classmethod
    def from_args(cls):
        model = StationOpModel()
        cls._set_model_common_fields(model, associated_station=VialSelectorStation.__name__)        
        model.save()
        return cls(model)

class VialSelectorStopStirringOp(StationOp):
    def __init__(self, station_op_model: Union[StationOpModel,ModelProxy]) -> None:
            super().__init__(station_op_model)

    @classmethod
    def from_args(cls):
        model = StationOpModel()
        cls._set_model_common_fields(model, associated_station=VialSelectorStation.__name__)        
        model.save()
        return cls(model)