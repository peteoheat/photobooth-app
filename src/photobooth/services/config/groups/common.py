"""
AppConfig class providing central config

"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, SerializationInfo, field_serializer

from ..serializer import contextual_serializer_password


class GroupCommon(BaseModel):
    """Common config for photobooth."""

    model_config = ConfigDict(title="Common Config")

    admin_password: SecretStr = Field(
        default=SecretStr("0000"),
        description="Password to access the admin dashboard.",
        min_length=4,
    )

    @field_serializer("admin_password")
    def contextual_serializer(self, value, info: SerializationInfo):
        return contextual_serializer_password(value, info)

    event_name: str = Field(
        default="",
        description="Name of the event. Captures, gallery, database and statistics are stored separately per event in ./events/<event_name>/. Leave empty to use the default location. Only letters, digits, - and _ are kept, others are replaced by _. A RESTART IS REQUIRED for a change to take effect! On Linux installs running as systemd service the app restarts automatically after saving, otherwise restart the app manually.",
        max_length=64,
    )

    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="DEBUG",
        description="Log verbosity. File is writte to disc, and latest log is displayed also in UI.",
    )

    users_delete_to_recycle_dir: bool = Field(
        default=True,
        description="If enabled, the captured files are moved to the recycle directory instead permanently deleted. Accidentally deleted images can be restored by the admin manually. Please inform users about the fact that no capture is deleted, if you enable the function!",
    )
