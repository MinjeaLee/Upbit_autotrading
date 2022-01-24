import time
import os
import sys
import logging
import traceback
 
from decimal import Decimal
 
# 공통 모듈 Import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from module import upbit
 
 
# -----------------------------------------------------------------------------
# - Name : start_buytrade
# - Desc : 매수 로직
# - Input
# 1) buy_amt : 매수금액
# 2) except_items : 매수 제외종목
# -----------------------------------------------------------------------------
def start_buytrade(buy_amt, except_items):
    try:
 
        #----------------------------------------------------------------------
        # 반복 수행
        #----------------------------------------------------------------------
        while True:
 
            logging.info("*********************************************************")
            logging.info("1. 로그레벨 : " + str(log_level))
            logging.info("2. 매수금액 : " + str(buy_amt))
            logging.info("3. 매수 제외종목 : " + str(except_items))
            logging.info("*********************************************************")
 
            #------------------------------------------------------------------
            # 매수 제외종목을 제외한 종목 리스트 추출
            #------------------------------------------------------------------
            target_items = upbit.get_items('KRW', except_items)
 
            for target_item in target_items:
 
                rsi_val = False
                mfi_val = False
                ocl_val = False
 
                logging.info('체크중....[' + str(target_item['market']) + ']')
 
                #--------------------------------------------------------------
                # 종목별 보조지표를 조회
                # 1. 조회 기준 : 일캔들, 최근 5개 지표 조회
                #--------------------------------------------------------------
                indicators_data = upbit.get_indicators(target_item['market'], 'D', 200, 5)
 
                #--------------------------------------------------------------
                # 최근 30일 이내에 신규 상장하여 보조 지표를 구하기 어려운 건은 제외
                #--------------------------------------------------------------
                if len(indicators_data) < 5:
                    logging.info('캔들 데이터 부족으로 매수 대상에서 제외....[' + str(target_item['market']) + ']')
                    continue
 
                #--------------------------------------------------------------
                # 매수 로직
                # 1. RSI : 2일전 < 30미만, 3일전 > 2일전, 1일전 > 2일전, 현재 > 1일전
                # 2. MFI : 2일전 < 20미만, 3일전 > 2일전, 1일전 > 2일전, 현재 > 1일전
                # 3. MACD(OCL) : 3일전 < 0, 2일전 < 0, 1일전 < 0, 3일전 > 2일전, 1일전 > 2일전, 현재 > 1일전
                #--------------------------------------------------------------
 
                #--------------------------------------------------------------
                # RSI : 2일전 < 30미만, 3일전 > 2일전, 1일전 > 2일전, 현재 > 1일전
                # indicators_data[0][0]['RSI'] : 현재
                # indicators_data[0][1]['RSI'] : 1일전
                # indicators_data[0][2]['RSI'] : 2일전
                # indicators_data[0][3]['RSI'] : 3일전
                #--------------------------------------------------------------
                if (Decimal(str(indicators_data[0][0]['RSI'])) > Decimal(str(indicators_data[0][1]['RSI']))
                    and Decimal(str(indicators_data[0][1]['RSI'])) > Decimal(str(indicators_data[0][2]['RSI']))
                    and Decimal(str(indicators_data[0][3]['RSI'])) > Decimal(str(indicators_data[0][2]['RSI']))
                    and Decimal(str(indicators_data[0][2]['RSI'])) < Decimal(str(30))):
                    rsi_val = True
 
                #--------------------------------------------------------------
                # MFI : 2일전 < 20미만, 3일전 > 2일전, 1일전 > 2일전, 현재 > 1일전
                # indicators_data[1][0]['MFI'] : 현재
                # indicators_data[1][1]['MFI'] : 1일전
                # indicators_data[1][2]['MFI'] : 2일전
                # indicators_data[1][3]['MFI'] : 3일전
                #--------------------------------------------------------------
                if (Decimal(str(indicators_data[1][0]['MFI'])) > Decimal(str(indicators_data[1][1]['MFI']))
                    and Decimal(str(indicators_data[1][1]['MFI'])) > Decimal(str(indicators_data[1][2]['MFI']))
                    and Decimal(str(indicators_data[1][3]['MFI'])) > Decimal(str(indicators_data[1][2]['MFI']))
                    and Decimal(str(indicators_data[1][2]['MFI'])) < Decimal(str(20))):
                    mfi_val = True
 
                #--------------------------------------------------------------
                # MACD(OCL) : 3일전 < 0, 2일전 < 0, 1일전 < 0, 3일전 > 2일전, 1일전 > 2일전, 현재 > 1일전
                # indicators_data[2][0]['OCL'] : 현재
                # indicators_data[2][1]['OCL'] : 1일전
                # indicators_data[2][2]['OCL'] : 2일전
                # indicators_data[2][3]['OCL'] : 3일전
                #--------------------------------------------------------------
                if (Decimal(str(indicators_data[2][0]['OCL'])) > Decimal(str(indicators_data[2][1]['OCL']))
                    and Decimal(str(indicators_data[2][1]['OCL'])) > Decimal(str(indicators_data[2][2]['OCL']))
                    and Decimal(str(indicators_data[2][3]['OCL'])) > Decimal(str(indicators_data[2][2]['OCL']))
                    and Decimal(str(indicators_data[2][1]['OCL'])) < Decimal(str(0))
                    and Decimal(str(indicators_data[2][2]['OCL'])) < Decimal(str(0))
                    and Decimal(str(indicators_data[2][3]['OCL'])) < Decimal(str(0))):
                    ocl_val = True
 
                #--------------------------------------------------------------
                # 매수대상 발견
                #--------------------------------------------------------------
                if rsi_val and mfi_val and ocl_val:
                    logging.info('매수대상 발견....[' + str(target_item['market']) + ']')
                    logging.info(indicators_data[0])
                    logging.info(indicators_data[1])
                    logging.info(indicators_data[2])
 
                    # ------------------------------------------------------------------
                    # 매수금액 설정
                    # 1. M : 수수료를 제외한 최대 가능 KRW 금액만큼 매수
                    # 2. 금액 : 입력한 금액만큼 매수
                    # ------------------------------------------------------------------
                    available_amt = upbit.get_krwbal()['available_krw']
 
                    if buy_amt == 'M':
                        buy_amt = available_amt
 
                    # ------------------------------------------------------------------
                    # 입력 금액이 주문 가능금액보다 작으면 종료
                    # ------------------------------------------------------------------
                    if Decimal(str(available_amt)) < Decimal(str(buy_amt)):
                        logging.info('주문 가능금액[' + str(available_amt) + ']이 입력한 주문금액[' + str(buy_amt) + '] 보다 작습니다.')
                        continue
 
                    # ------------------------------------------------------------------
                    # 최소 주문 금액(업비트 기준 5000원) 이상일 때만 매수로직 수행
                    # ------------------------------------------------------------------
                    if Decimal(str(buy_amt)) < Decimal(str(upbit.min_order_amt)):
                        logging.info('주문금액[' + str(buy_amt) + ']이 최소 주문금액[' + str(upbit.min_order_amt) + '] 보다 작습니다.')
                        continue
 
                    # ------------------------------------------------------------------
                    # 시장가 매수
                    # 실제 매수 로직은 안전을 위해 주석처리 하였습니다.
                    # 실제 매매를 원하시면 테스트를 충분히 거친 후 주석을 해제하시면 됩니다.
                    # ------------------------------------------------------------------
                    logging.info('시장가 매수 시작! [' + str(target_item['market']) + ']')
                    #rtn_buycoin_mp = upbit.buycoin_mp(target_item['market'], buy_amt)
                    logging.info('시장가 매수 종료! [' + str(target_item['market']) + ']')
                    #logging.info(rtn_buycoin_mp)
 
                    # ------------------------------------------------------------------
                    # 매수 완료 종목은 매수 대상에서 제외
                    # ------------------------------------------------------------------
                    if except_items.strip():
                        except_items = except_items + ',' + target_item['market'].split('-')[1]
                    else:
                        except_items = target_item['market'].split('-')[1]
 
    # ---------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise
 
# -----------------------------------------------------------------------------
# - Name : main
# - Desc : 메인
# -----------------------------------------------------------------------------
if __name__ == '__main__':
 
    # noinspection PyBroadException
    try:
 
        # ---------------------------------------------------------------------
        # 입력 받을 변수
        #
        # 1. 로그레벨
        #   1) 레벨 값 : D:DEBUG, E:ERROR, 그 외:INFO
        #
        # 2. 매수금액
        #   1) M : 수수료를 제외한 최대 가능 금액으로 매수
        #   2) 금액 : 입력한 금액만 매수(수수료 포함)
        #
        # 3. 매수 제외종목
        #   1) 종목코드(콤마구분자) : BTC,ETH
        # ---------------------------------------------------------------------
 
        # 1. 로그레벨
        log_level = input("로그레벨(D:DEBUG, E:ERROR, 그 외:INFO) : ").upper()
        buy_amt = input("매수금액(M:최대, 10000:1만원) : ").upper()
        except_items = input("매수 제외종목(종목코드, ex:BTC,ETH) : ").upper()
 
        upbit.set_loglevel(log_level)
 
        logging.info("*********************************************************")
        logging.info("1. 로그레벨 : " + str(log_level))
        logging.info("2. 매수금액 : " + str(buy_amt))
        logging.info("3. 매수 제외종목 : " + str(except_items))
        logging.info("*********************************************************")
 
        # 매수 로직 시작
        start_buytrade(buy_amt, except_items)
        
 
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-100)
 
    except Exception:
        logging.error("Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-200)