from interface import DiskSchedAlg
from collections import deque


class Fifo(DiskSchedAlg):
    def __init__(self):
        self.queue = deque()

    def put(self, request: [(str, (int, int))]):
        self.queue.append(request)

    def get_next(self):
        return self.queue.popleft()

    def is_scheduled(self, request: (str, (int, int))) -> bool:
        if request in self.queue:
            return True
        return False
