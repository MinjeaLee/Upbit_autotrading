import os
import sys
import logging
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
        # rtn_hoga = upbit.get_hoga('1000000')
        # logging.info(rtn_hoga)
 
        # rtn_target_price_hoga = upbit.get_targetprice('H', '1000000', '10')
        # rtn_target_price_rate = upbit.get_targetprice('R', '1000000', '10')
        # logging.info(rtn_target_price_hoga)
        # logging.info(rtn_target_price_rate)
 
    # # 잔고 조회(KRW, 소액 제외)
    #     account_data = upbit.get_accounts("Y", "KRW")
 
    #     for account_data_for in account_data:
    #         logging.info(account_data_for)
 
    #     logging.info('')
 
    #     # 잔고 조회(KRW, 소액 포함)
    #     account_data = upbit.get_accounts("N", "KRW")
 
    #     for account_data_for in account_data:
    #         logging.info(account_data_for)
            # 잔고 조회(KRW, 소액 제외)
        # krw_balance = upbit.get_krwbal()
 
        # logging.info(krw_balance)

        # candle_data =  upbit.get_candle('KRW-DOGE', '5', 5)

        # logging.info(len(candle_data))

        # for candle_data_for in candle_data:
        #     logging.info(candle_data_for)

        # # 보유 종목 리스트 조회
        # rsi_data = upbit.get_rsi('KRW-DOGE', '30', '200')
        # logging.info(rsi_data)

        # mfi_data = upbit.get_mfi('KRW-DOGE', '30', '200', 10)
 
        # for mfi_data_for in mfi_data:
        #     logging.info(mfi_data_for)

        # MACD 조회
        macd_data = upbit.get_macd('KRW-BTC', '30', '200', 10)
 
        for macd_data_for in macd_data:
            logging.info(macd_data_for)

    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(1)
 
    except Exception:
        logging.error("Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(1)