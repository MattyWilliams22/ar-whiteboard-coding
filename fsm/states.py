from enum import Enum, auto


class SystemState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PROJECTING = auto()
    ERROR = auto()
    EXITING = auto()


class Event(Enum):
    START_RUN = auto()
    FINISH_RUN = auto()
    CLEAR = auto()
    ERROR_OCCURRED = auto()
    EXIT = auto()
