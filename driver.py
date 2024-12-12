from config import hard_disk as disk_cnf


class HDDriver:
    def __init__(self):
        self.current_track = 0

    def send_request(self, request: (str, (int, int))):
        print(f"DRIVER: Sending {request} request to the disk")
        track = request[1][0]
        if track == self.current_track:
            print(f"DRIVER: Best decision: not to move")
            return disk_cnf.ROTATION_LATENCY_TIME + disk_cnf.SECTOR_ACCESS_TIME
        sequential_seek_time = abs(track-self.current_track) * disk_cnf.NEXT_TRACK_SEEK_TIME
        seek_time_with_rewind = disk_cnf.REWIND_SEEK_TIME + track * disk_cnf.NEXT_TRACK_SEEK_TIME
        self.current_track = track
        if sequential_seek_time < seek_time_with_rewind:
            print(f"DRIVER: Best decision: move sequentially")
            return sequential_seek_time + disk_cnf.ROTATION_LATENCY_TIME + disk_cnf.SECTOR_ACCESS_TIME
        else:
            print(f"DRIVER: Best decision: move with rewind")
            return seek_time_with_rewind + disk_cnf.ROTATION_LATENCY_TIME + disk_cnf.SECTOR_ACCESS_TIME

