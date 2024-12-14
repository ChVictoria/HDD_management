from config import scheduler as sched_cnf
from enum import Enum
from typing import List
from driver import HDDriver
from BC_management.interface import Cache
from HD_in_out_planning.interface import DiskSchedAlg


class OSMode(Enum):
    user = 0
    kernel = 1


class Event(Enum):
    request_completed = 0
    processing = 1
    syscall = 2


class Process:
    def __init__(self, name: str, requests: [(str, (int, int))]):
        self.name = name
        self.requests = requests  # the requests will be popped as processed


class Context:
    def __init__(self, process):
        self.process = process
        self.cur_mode: OSMode = OSMode.user
        self.cur_event: Event = Event.request_completed
        self.event_time_left = 0


class Interrupt:
    def __init__(self, timestamp, request: (str, (int, int))):
        self.timestamp = timestamp
        self.request = request
        self.time_left = sched_cnf.HD_INT_TIME


class Scheduler:
    def __init__(self, cache: Cache, disk_scheduler: DiskSchedAlg):
        self.driver = HDDriver()
        self.cache = cache
        self.disk_scheduler = disk_scheduler
        self.timestamp = 0
        self.runQ: List[Context] = []
        self.sleepQ: List[Context] = []
        self.next_int: Interrupt | None = None
        self.flushing_cache = 0

    def add_process(self, name, requests):
        new_process = Process(name, requests)
        self.runQ.append(Context(new_process))

    def handle_next_request(self, request):
        int_timestamp = self.driver.send_request(request) + self.timestamp
        self.next_int = Interrupt(int_timestamp, request)
        print(f"SCHEDULER: Next interrupt will be at {int_timestamp} us")

    def block_cur_process(self):
        cur_context = self.runQ.pop(0)
        self.sleepQ.append(cur_context)
        print(f"SCHEDULER: Block process {cur_context.process.name}")

    def wake_up_process(self, context):
        self.sleepQ.remove(context)
        self.runQ.append(context)
        print(f"SCHEDULER: Wake up process {context.process.name}")

    def handle_interrupt(self):
        waiting_buffer = self.next_int.request[1]
        in_out_type = self.next_int.request[0]
        in_out_name = 'READ' if in_out_type == 'r' else 'WRITE'
        print(f"SCHEDULER: Completed I/O ({in_out_name}) for buffer {waiting_buffer}")
        if in_out_type == 'r':
            popped_buffer = self.cache.put(data="some data", *waiting_buffer)
            if popped_buffer is not None:
                popped_request = ("w", (popped_buffer.track, popped_buffer.sector))
                self.disk_scheduler.put(popped_request)

            waking_up_processes = []
            for context in self.sleepQ:
                if context.process.requests[0] == self.next_int.request:
                    waking_up_processes.append(context)
            for context in waking_up_processes:
                self.wake_up_process(context)

        if self.flushing_cache:
            self.cache.pop(*self.next_int.request[1])
        self.cache.print_cache()

        next_request = self.disk_scheduler.get_next()
        self.disk_scheduler.print_state()
        if next_request:
            self.handle_next_request(next_request)
        else:
            self.next_int = None

    def execute_next_process(self):
        quantum_time_left = sched_cnf.QUANTUM_TIME
        context = self.runQ[0]
        mode = "User" if context.cur_mode == OSMode.user else "Kernel"
        print(f"SCHEDULER: {mode} mode for process {context.process.name}")
        while quantum_time_left != 0:
            next_int_timestamp = self.next_int.timestamp if self.next_int is not None else None
            request = context.process.requests[0]
            # processing next request if previous is completed
            if context.cur_event == Event.request_completed:
                match request[0]:
                    case "r":
                        context.cur_event = Event.syscall
                        context.event_time_left = sched_cnf.SYSCALL_READ_TIME
                        context.cur_mode = OSMode.kernel
                        print(f"SCHEDULER: Process {context.process.name} invoked read() for sector {request[1][1]} "
                              f"on track {request[1][0]}")
                        print(f"SCHEDULER: Kernel mode for process {context.process.name}")
                    case "w":
                        context.cur_event = Event.processing
                        context.event_time_left = sched_cnf.PROCESS_WRITING_TIME
                        context.cur_mode = OSMode.user
                continue
            else:
                # modeling interrupt
                if next_int_timestamp is not None:
                    time_to_int = next_int_timestamp - self.timestamp
                    if time_to_int <= context.event_time_left:
                        if time_to_int > quantum_time_left:
                            context.event_time_left -= quantum_time_left
                            self.timestamp += quantum_time_left
                            mode = "User" if context.cur_mode == OSMode.user else "Kernel"
                            print(f"SCHEDULER: ... worked for {quantum_time_left} us in {mode} mode")
                            break
                        else:
                            context.event_time_left -= time_to_int
                            print(f"SCHEDULER: ... worked for {time_to_int} us")
                            self.timestamp += time_to_int
                            quantum_time_left -= time_to_int
                            print("SCHEDULER: Interrupt from disk")
                            if self.next_int.time_left > quantum_time_left:
                                self.timestamp += quantum_time_left
                                print(f"SCHEDULER: ... worked for {quantum_time_left} us in interrupt handler")
                                self.next_int.timestamp = self.timestamp
                                self.next_int.time_left -= quantum_time_left
                                break
                            else:
                                int_time_left = self.next_int.time_left
                                self.handle_interrupt()
                                self.timestamp += int_time_left
                                quantum_time_left -= int_time_left
                                print(f"SCHEDULER: ... worked for {int_time_left} us in interrupt handler")
                                continue

                # working in event
                if context.event_time_left != 0:
                    if context.event_time_left > quantum_time_left:
                        context.event_time_left -= quantum_time_left
                        self.timestamp += quantum_time_left
                        mode = "User" if context.cur_mode == OSMode.user else "Kernel"
                        print(f"SCHEDULER: ... worked for {quantum_time_left} us in {mode} mode")
                        break
                    else:
                        self.timestamp += context.event_time_left
                        quantum_time_left -= context.event_time_left
                        mode = "User" if context.cur_mode == OSMode.user else "Kernel"
                        print(f"SCHEDULER: ... worked for {context.event_time_left} us in {mode} mode (completed)")
                        context.event_time_left = 0

                # processing and defining next event
                match context.cur_event:
                    case Event.syscall:
                        match request[0]:
                            case "r":
                                buffer = self.cache.get(request[1][0], request[1][1])
                                self.cache.print_cache()
                                if buffer is None:
                                    if self.next_int is None:
                                        self.disk_scheduler.put(request)
                                        request = self.disk_scheduler.get_next()
                                        self.handle_next_request(request)
                                    else:
                                        if self.next_int.request == request:
                                            print(f"SCHEDULER: Buffer {request[1]} is reading now")
                                        elif self.disk_scheduler.is_scheduled(request):
                                            print(f"SCHEDULER: Buffer {request[1]} is already scheduled for "
                                                  f"reading")
                                        else:
                                            self.disk_scheduler.put(request)
                                    self.disk_scheduler.print_state()
                                    self.block_cur_process()
                                    return
                                else:
                                    context.cur_event = Event.processing
                                    context.event_time_left = sched_cnf.PROCESS_READING_TIME
                                    context.cur_mode = OSMode.user
                                    print(f"SCHEDULER: User mode for process {context.process.name}")
                                    continue
                            case "w":
                                popped_buffer = self.cache.put(request[1][0], request[1][1], "some data")
                                self.cache.print_cache()
                                if popped_buffer is not None:
                                    popped_request = ("w", (popped_buffer.track, popped_buffer.sector))
                                    if self.next_int is None:
                                        self.handle_next_request(popped_request)
                                    else:
                                        self.disk_scheduler.put(popped_request)
                                    self.disk_scheduler.print_state()
                                context.process.requests.pop(0)
                                context.cur_event = Event.request_completed
                                context.event_time_left = 0
                                context.cur_mode = OSMode.user

                    case Event.processing:
                        match request[0]:
                            case "r":
                                context.process.requests.pop(0)
                                context.cur_event = Event.request_completed
                                context.event_time_left = 0
                                context.cur_mode = OSMode.user
                            case "w":
                                context.cur_event = Event.syscall
                                context.event_time_left = sched_cnf.SYSCALL_WRITE_TIME
                                context.cur_mode = OSMode.kernel
                                print(f"SCHEDULER: Process {context.process.name} invoked write() for sector "
                                      f"{request[1][1]} on track {request[1][0]}")
                                print(f"SCHEDULER: Kernel mode for process {context.process.name}")

                if len(self.runQ[0].process.requests) == 0:
                    print(f"SCHEDULER: Process {self.runQ[0].process.name} exited")
                    self.runQ.pop(0)
                    return
        self.runQ.append(self.runQ.pop(0))

    def flush_cache(self):
        cached_buffers = self.cache.list_buffers()
        first_buffer = cached_buffers.pop(0)
        self.handle_next_request(("w", first_buffer))
        for track, sector in cached_buffers:
            self.disk_scheduler.put(("w", (track, sector)))
        self.disk_scheduler.print_state()

    def start(self):
        while True:
            print(f"SCHEDULER: {self.timestamp} us (NEXT ITERATION)")
            if len(self.runQ) == 0:
                print("SCHEDULER: RunQ is empty")
                if self.next_int is not None:
                    print(f"SCHEDULER: Waiting for interrupt {self.next_int.timestamp - self.timestamp} us")
                    self.handle_interrupt()
                    self.timestamp += sched_cnf.HD_INT_TIME
                    print()
                    continue
                if not self.flushing_cache:
                    self.flushing_cache = True
                    print("SCHEDULER: All processes completed")
                    print("SCHEDULER: Flushing buffer cache")
                    self.flush_cache()
                    print()
                    continue
                else:
                    print("SCHEDULER: Have nothing to do, exit")
                    exit()
            else:
                self.execute_next_process()
            print()
