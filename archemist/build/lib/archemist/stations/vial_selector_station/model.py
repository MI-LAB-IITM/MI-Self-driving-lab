from archemist.core.models.station_model import StationModel
from archemist.core.models.station_op_model import StationOpModel
from mongoengine import fields
from enum import Enum, auto

class VialSelectorStationJobStatus(Enum):
    STIRRING = auto()
    VIAL_OPEN = auto()

class VialSelectorStationModel(StationModel):
    job_status = fields.EnumField(VialSelectorStationJobStatus, null=True)    

class VialSelectorStationOpModel(StationOpModel):
    vial_number = fields.IntField(default=0, min_value=0, max_value=12, null=False)
    aspiration_volume = fields.IntField(default=20, min_value=5, max_value=200, null=False)