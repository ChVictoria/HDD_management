from interface import DiskSchedAlg
from look import Look, LookDirection


class FLook(DiskSchedAlg):
    def __init__(self):
        self.active_look = Look()
        self.waiting_look = Look()

    def put(self, request: (str, (int, int))):
        self.waiting_look.put(request)

    def get_next(self):
        if len(self.active_look.queue) == 0:
            self.active_look, self.waiting_look = self.waiting_look, self.active_look
            self.active_look.cur_track = self.waiting_look.cur_track
            self.active_look.cur_direction = self.waiting_look.cur_direction
        next_req = self.active_look.get_next()
        return next_req

    def print_state(self):
        print("FLOOK: Current state")
        print(f"\tWaiting queue: {self.waiting_look.queue}")
        print(f"\tActive queue: {self.active_look.queue}")
        print("\tDirection:", end="")
        if self.active_look.cur_direction == LookDirection.asc:
            print("ascending")
        elif self.active_look.cur_direction == LookDirection.desc:
            print("descending")
        print(f"\tActive track: {self.active_look.cur_track}")

    def is_scheduled(self, request: (str, (int, int))) -> bool:
        if request in self.active_look.queue or request in self.waiting_look.queue:
            return True
        return False


if __name__ == "__main__":
    flook = FLook()
    flook.put(('r', (1, 100)))
    flook.print_state()
    flook.put(('r', (1, 14)))
    flook.put(('r', (2, 13)))
    flook.put(('r', (5, 80)))
    flook.put(('r', (3, 56)))
    flook.print_state()
    print(flook.get_next())
    flook.print_state()
    flook.put(('r', (4, 56)))
    flook.print_state()
    print(flook.get_next())
    flook.print_state()
    flook.put(('r', (3, 5)))
    flook.print_state()
    print(flook.get_next())
    flook.print_state()
    print(flook.get_next())
    flook.print_state()
    print(flook.get_next())
    flook.print_state()
    flook.put(('r', (1, 2)))
    flook.print_state()
    print(flook.get_next())
    flook.print_state()
