from archemist.core.models.station_model import StationModel
from archemist.core.models.station_op_model import StationOpModel
from mongoengine import fields
from enum import Enum, auto

class EZSpinA1SpinCoaterJobStatus(Enum):
    OPENING_LID = auto()
    OPENING_LID_COMPLETED = auto()
    LOADING_SUBSTRATE = auto()
    LOADING_SUBSTRATE_COMPLETED = auto()
    ASPIRATING_LIQUID = auto()
    ASPIRATING_LIQUID_COMPLETED = auto()
    DISPENSING_LIQUID = auto()
    DISPENSING_LIQUID_COMPLETED = auto()
    SPIN_COATING = auto()
    SPIN_COATING_COMPLETED = auto()
    CLOSING_LID = auto()
    CLOSING_LID_COMPLETED = auto()
    UNLOADING_SUBSTRATE =auto()
    UNLOADING_SUBSTRATE_COMPLETED =auto()

class EZSpinA1SpinCoaterStationModel(StationModel):
    job_status = fields.EnumField(EZSpinA1SpinCoaterJobStatus, null=True)

class EZSpinA1SpinCoaterOpModel(StationOpModel):
    current_substrate_ID = fields.IntField(default=0, min_value=0, max_value=1500, null=False)
    coating_rpm = fields.IntField(min_value=0, max_value=15000, null=True)
    coating_duration_in_seconds = fields.IntField(required=True)
    duration_unit = fields.StringField(default="second")
    volume_unit = fields.StringField(default="uL")