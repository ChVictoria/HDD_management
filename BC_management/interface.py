from abc import ABC


class Cache(ABC):
    def put(self, track, sector, data):
        pass

    def get(self, track, sector):
        pass

    def print_cache(self):
        pass

    def list_buffers(self) -> [(int, int)]:
        pass

    def pop(self, track, sector):
        pass