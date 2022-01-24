import os
import sys
import logging
import traceback
 
# 怨듯넻 紐⑤뱢 Import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from module import upbit as upbit  # noqa
 
# -----------------------------------------------------------------------------
# - Name : main
# - Desc : 硫붿씤
# -----------------------------------------------------------------------------
if __name__ == '__main__':
 
    # noinspection PyBroadException
    try:
 
        print("***** USAGE ******")
        print("[1] 로그레벨(D:DEBUG, E:ERROR, 그외:INFO)")
 
        upbit.set_loglevel('I')

    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 諛쒖깮!")
        logging.error(traceback.format_exc())
        sys.exit(1)
 
    except Exception:
        logging.error("Exception 諛쒖깮!")
        logging.error(traceback.format_exc())
        sys.exit(1)