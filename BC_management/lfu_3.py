from BC_management.interface import Cache
from typing import List, Dict
from collections import deque


class BufferData:
    def __init__(self, content):
        self.content = content


class Buffer:
    def __init__(self, track, sector, data):
        self.counter = 1
        self.track = track
        self.sector = sector
        self.data = BufferData(data)


class LFU(Cache):
    def __init__(self, left_len, middle_len, buffers_num):
        self.buffers_num = buffers_num
        self.left_len = left_len
        self.middle_len = middle_len
        self.buffers: List[Buffer] = []
        self.buffers_map: Dict[(int, int):Buffer] = dict()  # map track and segment numbers to buffers for get()
        self.right_counter_map: Dict[int:deque[(int, int)]] = dict()  # map counter to list of keys (track,
        # segment) for buffers having that counter in the right part of the buffers for effective pop() lfru buffer
        self.min_counter = 1

    def access_buffer(self, buffer):
        reversed_buffer_index = self.buffers.index(buffer)
        buffers_len = len(self.buffers)
        buffer_index = buffers_len - reversed_buffer_index - 1
        if buffer_index >= self.left_len:
            if buffer_index >= self.left_len + self.middle_len:
                print(f"CACHE: Buffer for sector {buffer.sector} on track {buffer.track} is in the right segment")
                self.right_counter_map[buffer.counter].remove((buffer.track, buffer.sector))
                self._add_next_to_right_counter_map()
                if buffer.counter == self.min_counter and len(self.right_counter_map[buffer.counter]) == 0:
                    self.right_counter_map.pop(buffer.counter)
                    self.min_counter = min(self.right_counter_map.keys())
            else:
                print(f"CACHE: Buffer for sector {buffer.sector} on track {buffer.track} is in the middle segment")
            buffer.counter += 1
        else:
            print(f"CACHE: Buffer for sector {buffer.sector} on track {buffer.track} is in the left segment")
        self.buffers.pop(reversed_buffer_index)
        self.buffers.append(buffer)

    def get(self, track, sector):
        buffer = self.buffers_map.get((track, sector))
        if buffer:
            print(f"CACHE: Buffer for sector {sector} on track {track} found in cache. Reading content.")
            self.access_buffer(buffer)
            return buffer.data
        print(f"CACHE: Buffer for sector {sector} on track {track} not found in cache")
        return None

    def _add_next_to_right_counter_map(self):
        shifted_buffer = self.buffers[len(self.buffers) - self.left_len - self.middle_len]
        if not self.right_counter_map.get(shifted_buffer.counter):
            self.right_counter_map[shifted_buffer.counter] = deque()
        self.right_counter_map[shifted_buffer.counter].append((shifted_buffer.track, shifted_buffer.sector))

    def put(self, track, sector, data):
        popped_buffer = None
        buffer = self.buffers_map.get((track, sector))
        if buffer:
            print(f"CACHE: Buffer for sector {sector} on track {track} found in cache. Modifying content.")
            buffer.data.content = data
            self.access_buffer(buffer)
            return None
        print(f"CACHE: Inserting to the cache new buffer for sector {sector} on track {track}")
        buffers_len = len(self.buffers)
        new_buffer = Buffer(track, sector, data)
        if buffers_len < self.buffers_num:
            print(f"CACHE: There are free buffers available")
            if buffers_len >= self.left_len+self.middle_len:
                self._add_next_to_right_counter_map()
        else:
            lfru_track, lfru_sector = self.right_counter_map[self.min_counter][0]
            print(f"CACHE: No free buffers, freeing the least frequently and least recently used buffer of sector "
                  f"{lfru_sector} on track {lfru_track}")
            popped_buffer = self.buffers_map.pop((lfru_track, lfru_sector))
            self.buffers.remove(popped_buffer)
            self.right_counter_map[self.min_counter].popleft()
            if len(self.right_counter_map[self.min_counter]) == 0:
                self.right_counter_map.pop(self.min_counter)
                self.min_counter = min(self.right_counter_map.keys())
            self._add_next_to_right_counter_map()
        self.buffers.append(new_buffer)
        self.buffers_map[(track, sector)] = new_buffer
        return popped_buffer

    def print_cache(self):
        print("CACHE: Current buffers\n\t[ ", end="")
        for i in range(len(self.buffers)-1, -1, -1):
            if i == len(self.buffers) - self.left_len - 1 or \
               i == len(self.buffers) - self.left_len - self.middle_len - 1:
                print("| ", end="")
            print(self.buffers[i].track, ":", self.buffers[i].sector, " c=", self.buffers[i].counter, ", ",
                  sep="", end="")
        print(" ]")

    def pop(self, track, sector):
        if (track, sector) in self.buffers_map:
            print(f"CACHE: Remove buffer for sector {sector} on track {track} from cache")
            popped_buffer = self.buffers_map.pop((track, sector))
            reversed_buffer_index = self.buffers.index(popped_buffer)
            buffer_index = len(self.buffers) - reversed_buffer_index - 1
            del self.buffers[reversed_buffer_index]
            if buffer_index >= self.left_len+self.middle_len:
                self.right_counter_map[popped_buffer.counter].remove((track, sector))
            return popped_buffer.data
        return None

    def list_buffers(self):
        return list(self.buffers_map.keys())


if __name__ == "__main__":
    lfu = LFU(4, 3, 10)
    lfu.put(2, 135, "data")
    lfu.print_cache()
    print(lfu.get(2, 135))
    lfu.print_cache()
    lfu.put(2, 129, "data")
    lfu.print_cache()
    lfu.put(2, 4, "data")
    lfu.print_cache()
    lfu.put(1, 13, "data")
    lfu.print_cache()
    lfu.put(1, 48, "data")
    lfu.print_cache()
    lfu.put(1, 242, "data")
    lfu.print_cache()
    lfu.put(2, 1, "data")
    lfu.print_cache()
    lfu.put(1, 100, "data")
    lfu.print_cache()
    lfu.put(1, 28, "data")
    lfu.print_cache()
    print(lfu.get(1, 48))
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 8, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 155, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 15, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 16, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 17, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 18, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 19, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 20, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 21, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
    lfu.put(2, 22, "data")
    lfu.print_cache()
    print(lfu.right_counter_map)
