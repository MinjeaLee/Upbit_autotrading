import os
import sys
import logging
import math
import traceback
 
# 공통 모듈 Import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from module import upbit as upbit  # noqa
 
# -----------------------------------------------------------------------------
# - Name : main
# - Desc : 메인
# -----------------------------------------------------------------------------
if __name__ == '__main__':
 
    # noinspection PyBroadException
    try:
 
        print("***** USAGE ******")
        print("[1] 로그레벨(D:DEBUG, E:ERROR, 그외:INFO)")
 
        # 로그레벨(D:DEBUG, E:ERROR, 그외:INFO)
        upbit.set_loglevel('I')
 
        # ---------------------------------------------------------------------
        # Logic Start!
        # ---------------------------------------------------------------------
        # 전 종목 리스트 조회
        item_list = upbit.get_items('KRW', '')
 
        logging.info(len(item_list))
        logging.info(item_list)
 
        # 원화 매수 가능 금액 조회
        krw_bal = upbit.get_krwbal()
 
        logging.info(krw_bal)
 
        # 💚종목별 매수 금액 설정(일정 금액 직접 입력)
        #item_buy_amt = 5000
 
        # 종목별 매수 금액 설정(KRW잔고 이용)
        item_buy_amt = math.floor(krw_bal['available_krw'] / len(item_list))
 
        logging.info(item_buy_amt)
 
        # 종목별 처리
        for item_list_for in item_list:
 
            logging.info('종목코드:' + item_list_for['market'])
 
            # 시장가 매수
            # 💚 실제 매수가 될 수 있어 아래 주석 처리함.
            #upbit.buycoin_mp(item_list_for['market'], item_buy_amt)
 
        logging.info('전 종목 매수 완료')        
 
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(1)
 
    except Exception:
        logging.error("Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(1)