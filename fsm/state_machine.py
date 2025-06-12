from threading import Lock
from .states import SystemState, Event


class SystemFSM:
    def __init__(self):
        self.state = SystemState.IDLE
        self.lock = Lock()
        self._initialise_transitions()

    def _initialise_transitions(self):
        """Initialise the state transitions for the FSM."""
        self.transitions = {
            SystemState.IDLE: {
                Event.START_RUN: SystemState.RUNNING,
                Event.ERROR_OCCURRED: SystemState.ERROR,
                Event.EXIT: SystemState.EXITING,
            },
            SystemState.RUNNING: {
                Event.CLEAR: SystemState.IDLE,
                Event.FINISH_RUN: SystemState.PROJECTING,
                Event.ERROR_OCCURRED: SystemState.ERROR,
                Event.EXIT: SystemState.EXITING,
            },
            SystemState.PROJECTING: {
                Event.CLEAR: SystemState.IDLE,
                Event.START_RUN: SystemState.RUNNING,
                Event.ERROR_OCCURRED: SystemState.ERROR,
                Event.EXIT: SystemState.EXITING,
            },
            SystemState.ERROR: {
                Event.CLEAR: SystemState.IDLE,
                Event.START_RUN: SystemState.RUNNING,
                Event.EXIT: SystemState.EXITING,
            },
        }

    def transition(self, event):
        """Transition to the next state based on the current state and event."""
        with self.lock:
            print(f"Current state: {self.state}, Event: {event}")
            if event in self.transitions[self.state]:
                self.state = self.transitions[self.state][event]
                print(f"Transitioned to {self.state} state.")
                return True
            return False
