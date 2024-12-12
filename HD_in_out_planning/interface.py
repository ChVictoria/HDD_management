from abc import ABC


class DiskSchedAlg(ABC):
    def put(self, request: (str, (int, int))):
        pass

    def get_next(self) -> (str, (int, int)):
        pass

    def print_state(self):
        pass

    def is_scheduled(self, request: (str, (int, int))) -> bool:
        pass
