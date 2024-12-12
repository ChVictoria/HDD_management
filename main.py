#from HD_in_out_planning.fifo import Fifo
from HD_in_out_planning.look import Look
#from HD_in_out_planning.flook import FLook
from BC_management.lfu_3 import LFU
from scheduler import Scheduler

from config import cache as cache_cnf

os_scheduler = Scheduler(LFU(cache_cnf.LFU_LEFT_LEN, cache_cnf.LFU_MIDDLE_LEN, cache_cnf.BUFFERS_NUM), Look())
os_scheduler.add_process("ps1", [("r", (1, 100)), ("w", (2, 10)), ("r", (1, 203))])
os_scheduler.add_process("ps2", [("w", (1, 200)), ("w", (1, 100)), ("r", (1, 203))])
os_scheduler.start()