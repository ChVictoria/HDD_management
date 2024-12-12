from HD_in_out_planning.interface import DiskSchedAlg
from enum import Enum


class LookDirection(Enum):
    asc = 0
    desc = 1


class Look(DiskSchedAlg):
    def __init__(self):
        self.queue = []
        self.cur_direction = LookDirection.asc
        self.cur_track = 0

    def _search_index_to_insert(self, track):
        if track > self.queue[len(self.queue)-1][1][0]:
            return len(self.queue)
        if track <= self.queue[0][1][0]:
            return 0
        low = 0
        high = len(self.queue) - 1
        while low < high - 1:
            mid = low + ((high - low) >> 1)
            if self.queue[mid][1][0] <= track:
                low = mid + 1
            else:
                high = mid - 1

        return high

    def put(self, request: (str, (int, int))):
        if len(self.queue) == 0:
            self.queue.append(request)
        else:
            index = self._search_index_to_insert(request[1][0])
            self.queue.insert(index, request)

    def get_next(self):
        if len(self.queue) == 0:
            return None
        ins_index = self._search_index_to_insert(self.cur_track)
        if self.cur_direction == LookDirection.asc:
            if ins_index == len(self.queue):
                self.cur_direction = LookDirection.desc
                next_req = self.queue.pop(ins_index-1)
            else:
                next_req = self.queue.pop(ins_index)
        elif self.cur_direction == LookDirection.desc:
            if ins_index == 0:
                self.cur_direction = LookDirection.asc
                next_req = self.queue.pop(ins_index)
            else:
                next_req = self.queue.pop(ins_index-1)
        self.cur_track = next_req[1][0]
        return next_req

    def print_state(self):
        print("LOOK: Current state")
        print(f"\tQueue: {self.queue}")
        print("\tDirection: ", end="")
        if self.cur_direction == LookDirection.asc:
            print("ascending")
        elif self.cur_direction == LookDirection.desc:
            print("descending")
        print(f"\tActive track: {self.cur_track}")

    def is_scheduled(self, request: (str, (int, int))) -> bool:
        if request in self.queue:
            return True
        return False


if __name__ == "__main__":
    look = Look()
    look.put((1, 100))
    look.print_state()
    look.put((1, 145))
    look.put((2, 130))
    look.put((5, 80))
    look.put((3, 56))
    look.put((10, 56))
    look.put((7, 56))
    look.print_state()
    print(look.get_next())
    look.print_state()
    print(look.get_next())
    look.print_state()
    print(look.get_next())
    look.print_state()
