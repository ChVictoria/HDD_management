from HD_in_out_planning.interface import DiskSchedAlg
from collections import deque


class Fifo(DiskSchedAlg):
    def __init__(self):
        self.queue = deque()

    def put(self, request: [(str, (int, int))]):
        self.queue.append(request)

    def get_next(self):
        if len(self.queue) != 0:
            return self.queue.popleft()
        return None

    def is_scheduled(self, request: (str, (int, int))) -> bool:
        if request in self.queue:
            return True
        return False

    def print_state(self):
        print(f"FIFO: Current queue\n\t{list(self.queue)}")
