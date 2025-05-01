from threading import Lock
from .states import SystemState, Event

class SystemFSM:
    def __init__(self):
        self.state = SystemState.IDLE
        self.lock = Lock()
        self._initialize_transitions()

    def _initialize_transitions(self):
        self.transitions = {
            SystemState.IDLE: {
                Event.START_RUN: SystemState.RUNNING,
                Event.OPEN_SETTINGS: SystemState.SETTINGS,
                Event.ERROR: SystemState.ERROR,
                Event.EXIT: SystemState.EXITING
            },
            SystemState.RUNNING: {
                Event.STOP_RUN: SystemState.IDLE,
                Event.TOGGLE_PROJECT: SystemState.PROJECTING,
                Event.OPEN_SETTINGS: SystemState.SETTINGS,
                Event.ERROR: SystemState.ERROR,
                Event.EXIT: SystemState.EXITING
            },
            SystemState.PROJECTING: {
                Event.STOP_RUN: SystemState.IDLE,
                Event.START_RUN: SystemState.RUNNING,
                Event.OPEN_SETTINGS: SystemState.SETTINGS,
                Event.ERROR: SystemState.ERROR,
                Event.EXIT: SystemState.EXITING
            },
            SystemState.SETTINGS: {
                Event.CLOSE_SETTINGS: SystemState.IDLE,
                Event.ERROR: SystemState.ERROR,
                Event.EXIT: SystemState.EXITING
            },
            SystemState.ERROR: {
                Event.RESOLVED: SystemState.IDLE,
                Event.OPEN_SETTINGS: SystemState.SETTINGS,
                Event.EXIT: SystemState.EXITING
            }
        }

    def transition(self, event):
        with self.lock:
            if event in self.transitions[self.state]:
                self.state = self.transitions[self.state][event]
                return True
            return False