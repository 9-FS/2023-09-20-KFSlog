import logging
import sys
import traceback

sys.path.append("./")   # enables importing via parent directory
from KFSlog import KFSlog


@KFSlog.timeit
def test() -> None:
    
    
    return


#KFSlog.setup_logging("", logging.INFO)
KFSlog.setup_logging("", logging.DEBUG, filepath_format="./log/%Y-%m-%dT%H_%M.log", rotate_filepath_when="M")

try:
    test()
except:
    logging.critical(traceback.format_exc())
    print("\nPress enter to close program.", flush=True)
    input() # pause