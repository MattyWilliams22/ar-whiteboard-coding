from enum import Enum, auto

class SystemState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PROJECTING = auto()
    SETTINGS = auto()
    ERROR = auto()
    EXITING = auto()

class Event(Enum):
    START_RUN = auto()
    STOP_RUN = auto()
    TOGGLE_PROJECT = auto()
    OPEN_SETTINGS = auto()
    CLOSE_SETTINGS = auto()
    ERROR = auto()
    RESOLVED = auto()
    EXIT = auto()