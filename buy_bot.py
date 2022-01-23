import sys
import logging
import traceback

from module import upbit
 
 
# -----------------------------------------------------------------------------
# - Name : main
# - Desc : 메인
# -----------------------------------------------------------------------------
if __name__ == '__main__':
 
    # noinspection PyBroadException
    try:
        # # 로그레벨 설정(DEBUG)
        # upbit.set_loglevel('D')
 
        # # 종목 조회
        # item_list = upbit.get_items("KRW", "BTC")
 
        # # 결과 출력
        # logging.info(item_list)
                # 로그레벨 설정(DEBUG)
        upbit.set_loglevel('I')
        
        # 주문가능 잔고 조회
        balance = upbit.get_balance('KRW-DOGE')
        
        # 잔고 출력
        logging.info(balance)
 
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(1)
 
    except Exception:
        logging.error("Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(1)