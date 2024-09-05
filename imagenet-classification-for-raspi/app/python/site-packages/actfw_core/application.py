import json
import os
import signal
import sys
import time
from types import FrameType
from typing import Any, Dict, Iterable, List, Optional

from actfw_core.task import Task


class SettingSchema:
    def __init__(
        self,
        title: str,
        description: str,
        type_: type,
        default: Any = None,
        ui_type: Optional[str] = None,
    ):
        self.title = title
        self.description = description
        self.type = type_
        self.default = default
        self.ui_type = ui_type

    @staticmethod
    def decoder(obj: Any) -> Any:
        if "title" in obj and "description" in obj and "type" in obj:
            return SettingSchema(
                obj["title"],
                obj["description"],
                SettingSchema.infertype(obj["type"]),
                obj.get("default", None),
                obj.get("x-ui-type"),
            )
        return obj

    @staticmethod
    def infertype(typestring: str) -> type:
        if typestring == "number":
            return float
        elif typestring == "integer":
            return int
        elif typestring == "boolean":
            return bool
        else:
            return str


class AppSettings:
    def __init__(self, settings: Dict[str, Any], schema: Dict[str, SettingSchema]):
        self.settings = settings
        self.schema = schema

    def __getattr__(self, name: str) -> Any:
        if name in self.settings:
            if isinstance(self.settings[name], self.schema[name].type):
                return self.settings[name]
            elif self.schema[name].default is not None:
                print(
                    f"Invalid type for setting:{name}. Using schema default value.",
                    file=sys.stderr,
                    flush=True,
                )
                return self.schema[name].default
            else:
                print(f"Invalid type of {name}: {type(name)}", file=sys.stderr, flush=True)
        elif name in self.schema:
            print(
                f"Setting:{name} not found. Using schema default value.",
                file=sys.stderr,
                flush=True,
            )
            return self.schema[name].default
        else:
            raise AttributeError(f"{name} is not found in settings.")

    def __repr__(self) -> str:
        values = []
        for key, schema in self.schema.items():
            if schema.ui_type == "password":
                values.append(f"{key}=***")
            else:
                values.append(f"{key}={getattr(self, key)}")
        return f"AppSettings({', '.join(values)})"


class Application:
    running: bool
    tasks: List[Task]
    settings: Optional[Dict[str, Any]]

    """Actcast Application"""

    def __init__(
        self,
        stop_by_signals: Iterable[signal.Signals] = (signal.SIGINT, signal.SIGTERM),
    ) -> None:
        self.running = True
        for sig in stop_by_signals:
            signal.signal(sig, self._handler)  # type: ignore[arg-type]
        self.tasks = []
        self.settings = None
        env = "ACT_SETTINGS_PATH"
        if env in os.environ:
            try:
                with open(os.environ[env]) as f:
                    self.settings = json.load(f)
            except FileNotFoundError:
                pass

    def _handler(self, sig: signal.Signals, frame: FrameType) -> None:
        self.stop()

    def get_settings(self, default_settings: Dict[str, Any]) -> Dict[str, Any]:
        """

        Get given Act settings.

        Args:
            default_settings (dict): default settings

        Returns:
            dict: updated settings

        Notes:
            Copy default_settings and overwrite it by given Act settings.

        """
        if not isinstance(default_settings, dict):
            raise TypeError("default_settings must be dict.")
        settings = default_settings.copy()
        if self.settings is not None:
            settings.update(self.settings)
        return settings

    def get_app_settings(self, path: str = "setting_schema.json") -> AppSettings:
        """
        Get application settings from schema.
        Args:
            path (str): path to schema file
        Returns:
            AppSettings: application settings
        """
        with open(path) as f:
            self.schema = json.load(f, object_hook=SettingSchema.decoder)["properties"]
        return AppSettings(self.get_settings({}), self.schema)

    def register_task(self, task: Task) -> None:
        """

        Register the application task.

        Args:
            task (:class:`~actfw_core.task.Task`): task
        """
        if not issubclass(type(task), Task):
            raise TypeError("type(task) must be a subclass of actfw_core.task.Task.")
        self.tasks.append(task)

    def run(self) -> None:
        """Start application"""
        for task in self.tasks:
            task.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        for task in self.tasks:
            task.stop()
        for task in self.tasks:
            task.join()

    def stop(self) -> None:
        """Stop application"""
        self.running = False
