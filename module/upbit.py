import time
import logging
import requests
import jwt
import uuid
import hashlib
import math
import os
import numpy
import pandas as pd
import sys
import smtplib
 
from urllib.parse import urlencode
from decimal import Decimal
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Keys
load_dotenv() # 환경 변수 호출 부분

access_key = os.environ.get('access_key')
secret_key = os.environ.get('secret_key')
server_url = 'https://api.upbit.com'

# 최소 주문 금액
min_order_amt = 5000
 
# -----------------------------------------------------------------------------
# - Name : set_loglevel
# - Desc : 로그레벨 설정
# - Input
#   1) level : 로그레벨
#     1. D(d) : DEBUG
#     2. E(e) : ERROR
#     3. 그외(기본) : INFO
# - Output
# -----------------------------------------------------------------------------
def set_loglevel(level):
    try:
 
        # ---------------------------------------------------------------------
        # 로그레벨 : DEBUG
        # ---------------------------------------------------------------------
        if level.upper() == "D":
            logging.basicConfig(
                format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]:%(message)s',
                datefmt='%Y/%m/%d %I:%M:%S %p',
                level=logging.DEBUG
            )
        # ---------------------------------------------------------------------
        # 로그레벨 : ERROR
        # ---------------------------------------------------------------------
        elif level.upper() == "E":
            logging.basicConfig(
                format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]:%(message)s',
                datefmt='%Y/%m/%d %I:%M:%S %p',
                level=logging.ERROR
            )
        # ---------------------------------------------------------------------
        # 로그레벨 : INFO
        # ---------------------------------------------------------------------
        else:
            # -----------------------------------------------------------------------------
            # 로깅 설정
            # 로그레벨(DEBUG, INFO, WARNING, ERROR, CRITICAL)
            # -----------------------------------------------------------------------------
            logging.basicConfig(
                format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]:%(message)s',
                datefmt='%Y/%m/%d %I:%M:%S %p',
                level=logging.INFO
            )
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise
 
# -----------------------------------------------------------------------------
# - Name : send_request
# - Desc : 리퀘스트 처리
# - Input
#   1) reqType : 요청 타입
#   2) reqUrl : 요청 URL
#   3) reqParam : 요청 파라메타
#   4) reqHeader : 요청 헤더
# - Output
#   4) reponse : 응답 데이터
# -----------------------------------------------------------------------------
def send_request(reqType, reqUrl, reqParam, reqHeader):
    try:
 
        # 요청 가능회수 확보를 위해 기다리는 시간(초)
        err_sleep_time = 0.3 #! 1 --> 0.3
 
        # 요청에 대한 응답을 받을 때까지 반복 수행
        while True:
 
            # 요청 처리
            response = requests.request(reqType, reqUrl, params=reqParam, headers=reqHeader)
 
            # 요청 가능회수 추출
            if 'Remaining-Req' in response.headers:
 
                hearder_info = response.headers['Remaining-Req']
                start_idx = hearder_info.find("sec=")
                end_idx = len(hearder_info)
                remain_sec = hearder_info[int(start_idx):int(end_idx)].replace('sec=', '')
            else:
                logging.error("헤더 정보 이상")
                logging.error(response.headers)
                break
 
            # 요청 가능회수가 4개 미만이면 요청 가능회수 확보를 위해 일정시간 대기
            if int(remain_sec) < 3:     #! 4 --> 3
                logging.debug("요청 가능회수 한도 도달! 남은횟수:" + str(remain_sec))
                time.sleep(err_sleep_time)
 
            # 정상 응답
            if response.status_code == 200 or response.status_code == 201:
                break
            # 요청 가능회수 초과인 경우
            elif response.status_code == 429:
                logging.error("요청 가능회수 초과!:" + str(response.status_code))
                time.sleep(err_sleep_time)
            # 그 외 오류
            else:
                logging.error("기타 에러:" + str(response.status_code))
                logging.error(response.status_code)
                break
 
            # 요청 가능회수 초과 에러 발생시에는 다시 요청
            logging.info("[restRequest] 요청 재처리중...")
 
        return response
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise
 
# -----------------------------------------------------------------------------
# - Name : get_items
# - Desc : 전체 종목 리스트 조회
# - Input
#   1) market : 대상 마켓(콤마 구분자:KRW,BTC,USDT)
#   2) except_item : 제외 종목(콤마 구분자:BTC,ETH)
# - Output
#   1) 전체 리스트 : 리스트
# -----------------------------------------------------------------------------
def get_items(market, except_item):
    try:
 
        # 조회결과 리턴용
        rtn_list = []
 
        # 마켓 데이터
        markets = market.split(',')
 
        # 제외 데이터
        except_items = except_item.split(',')
 
        url = "https://api.upbit.com/v1/market/all"
        querystring = {"isDetails": "false"}
        response = send_request("GET", url, querystring, "")
        data = response.json()
 
        # 조회 마켓만 추출
        for data_for in data:
            for market_for in markets:
                if data_for['market'].split('-')[0] == market_for:
                    rtn_list.append(data_for)
 
        # 제외 종목 제거
        for rtnlist_for in rtn_list[:]:
            for exceptItemFor in except_items:
                for marketFor in markets:
                    if rtnlist_for['market'] == marketFor + '-' + exceptItemFor:
                        rtn_list.remove(rtnlist_for)
 
        return rtn_list
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

    
# -----------------------------------------------------------------------------
# - Name : buycoin_mp
# - Desc : 시장가 매수
# - Input
#   1) target_item : 대상종목
#   2) buy_amount : 매수금액
# - Output
#   1) rtn_data : 매수결과
# -----------------------------------------------------------------------------
def buycoin_mp(target_item, buy_amount):
    try:
 
        query = {
            'market': target_item,
            'side': 'bid',
            'price': buy_amount,
            'ord_type': 'price',
        }
 
        query_string = urlencode(query).encode()
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("POST", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()
 
        logging.info("")
        logging.info("----------------------------------------------")
        logging.info("시장가 매수 완료!")
        logging.info(rtn_data)
        logging.info("----------------------------------------------")
 
        return rtn_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_balance
# - Desc : 주문가능 잔고 조회
# - Input
#   1) target_item : 대상 종목
# - Output
#   2) rtn_balance : 주문가능 잔고
# -----------------------------------------------------------------------------
def get_balance(target_item):
    try:
 
        # 주문가능 잔고 리턴용
        rtn_balance = 0
 
        # 최대 재시도 횟수
        max_cnt = 0
 
        # 잔고가 조회 될 때까지 반복
        while True:
 
            # 조회 회수 증가
            max_cnt = max_cnt + 1
 
            payload = {
                'access_key': access_key,
                'nonce': str(uuid.uuid4()),
            }
 
            jwt_token = jwt.encode(payload, secret_key)
            authorize_token = 'Bearer {}'.format(jwt_token)
            headers = {"Authorization": authorize_token}
 
            res = send_request("GET", server_url + "/v1/accounts", "", headers)
            my_asset = res.json()

            # print(my_asset) 테스트용 print
 
            # 해당 종목에 대한 잔고 조회
            # 잔고는 마켓에 상관없이 전체 잔고가 조회됨
            for myasset_for in my_asset:
                if myasset_for['currency'] == target_item.split('-')[1]:
                    rtn_balance = myasset_for['balance']
 
            # 잔고가 0 이상일때까지 반복
            if Decimal(str(rtn_balance)) > Decimal(str(0)):
                break
 
            # 최대 100회 수행
            if max_cnt > 100:
                break
 
            logging.info("[주문가능 잔고 리턴용] 요청 재처리중...")
 
        return rtn_balance
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : cancel_order
# - Desc : 미체결 주문 취소
# - Input
#   1) target_item : 대상종목
#   2) side : 매수/매도 구분(BUY/bid:매수, SELL/ask:매도, ALL:전체)
# - Output
# -----------------------------------------------------------------------------
def cancel_order(target_item, side):
    try:
 
        # 미체결 주문 조회
        order_data = get_order(target_item)
 
        # 매수/매도 구분
        for order_data_for in order_data:
 
            if side == "BUY" or side == "buy":
                if order_data_for['side'] == "ask":
                    order_data.remove(order_data_for)
            elif side == "SELL" or side == "sell":
                if order_data_for['side'] == "bid":
                    order_data.remove(order_data_for)
 
        # 미체결 주문이 있으면
        if len(order_data) > 0:
 
            # 미체결 주문내역 전체 취소
            for order_data_for in order_data:
                cancel_order_uuid(order_data_for['uuid'])
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise


# -----------------------------------------------------------------------------
# - Name : cancel_order_uuid
# - Desc : 미체결 주문 취소 by UUID
# - Input
#   1) order_uuid : 주문 키
# - Output
#   1) 주문 내역 취소
# -----------------------------------------------------------------------------
def cancel_order_uuid(order_uuid):
    try:
 
        query = {
            'uuid': order_uuid,
        }
 
        query_string = urlencode(query).encode()
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("DELETE", server_url + "/v1/order", query, headers)
        rtn_data = res.json()
 
        return rtn_data
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise


# -----------------------------------------------------------------------------
# - Name : sellcoin_mp
# - Desc : 시장가 매도
# - Input
#   1) target_item : 대상종목
# - Output
#   1) rtn_data : 매도결과
# -----------------------------------------------------------------------------
# 시장가 매도
def sellcoin_mp(target_item, cancel_yn): #todo 제외 종목도 매수 되는지 확인
    
    try:

        if cancel_yn == 'Y' or cancel_yn == 'y':  #! 이부분 없었는데 생김   
            # 기존 주문 존재시 취소
            cancel_order(target_item, "SELL")
       
 
        # 잔고 조회
        cur_balance = get_balance(target_item)
 
        query = {
            'market': target_item,
            'side': 'ask',
            'volume': cur_balance,
            'ord_type': 'market',
        }
 
        query_string = urlencode(query).encode()
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("POST", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()
 
        logging.info("")
        logging.info("----------------------------------------------")
        logging.info("시장가 매도 완료!")
        logging.info(rtn_data)
        logging.info("----------------------------------------------")
 
        return rtn_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : sellcoin_tg
# - Desc : 지정가 매도
# - Input
#   1) target_item : 대상종목
#   2) sell_price : 매도희망금액
# - Output
#   1) rtn_data : 매도결과
# -----------------------------------------------------------------------------
def sellcoin_tg(target_item, sell_price):        #todo sellcoin_mp와 마찬가지로 제외 종목도 매수되는지 확인 
    try:
 
        # 잔고 조회
        cur_balance = get_balance(target_item)

        query = {
            'market': target_item,
            'side': 'ask',
            'volume': cur_balance,
            'price': sell_price,
            'ord_type': 'limit',
        }
 
        query_string = urlencode(query).encode()    #? 전량 매도 
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("POST", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()
 
        logging.info("")
        logging.info("----------------------------------------------")
        logging.info("지정가 매도 설정 완료!")
        logging.info(rtn_data)
        logging.info("----------------------------------------------")
 
        return rtn_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_hoga
# - Desc : 호가 금액 계산
# - Input
#   1) cur_price : 현재가격
# - Output
#   1) hoga_val : 호가단위
# -----------------------------------------------------------------------------
def get_hoga(cur_price):
    try:
 
        # 호가 단위
        if Decimal(str(cur_price)) < 10:
            hoga_val = 0.01
        elif Decimal(str(cur_price)) < 100:
            hoga_val = 0.1
        elif Decimal(str(cur_price)) < 1000:
            hoga_val = 1
        elif Decimal(str(cur_price)) < 10000:
            hoga_val = 5
        elif Decimal(str(cur_price)) < 100000:
            hoga_val = 10
        elif Decimal(str(cur_price)) < 500000:
            hoga_val = 50
        elif Decimal(str(cur_price)) < 1000000:
            hoga_val = 100
        elif Decimal(str(cur_price)) < 2000000:
            hoga_val = 500
        else:
            hoga_val = 1000
 
        return hoga_val
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_targetprice
# - Desc : 호가단위 금액 계산
# - Input
#   1) cal_type : H:호가로, R:비율로
#   2) st_price : 기준가격
#   3) chg_val : 변화단위
# - Output
#   1) rtn_price : 계산된 금액
# -----------------------------------------------------------------------------
def get_targetprice(cal_type, st_price, chg_val):
    try:
        # 계산된 가격
        rtn_price = st_price
 
        # 호가단위로 계산
        if cal_type.upper() == "H":
 
            for i in range(0, abs(int(chg_val))):
 
                hoga_val = get_hoga(rtn_price)
 
                if Decimal(str(chg_val)) > 0:
                    rtn_price = Decimal(str(rtn_price)) + Decimal(str(hoga_val))
                elif Decimal(str(chg_val)) < 0:
                    rtn_price = Decimal(str(rtn_price)) - Decimal(str(hoga_val))
                else:
                    break
 
        # 비율로 계산
        elif cal_type.upper() == "R":
 
            while True:
 
                # 호가단위 추출
                hoga_val = get_hoga(st_price)
 
                if Decimal(str(chg_val)) > 0:
                    rtn_price = Decimal(str(rtn_price)) + Decimal(str(hoga_val))
                elif Decimal(str(chg_val)) < 0:
                    rtn_price = Decimal(str(rtn_price)) - Decimal(str(hoga_val))
                else:
                    break
 
                if Decimal(str(chg_val)) > 0:
                    if Decimal(str(rtn_price)) >= Decimal(str(st_price)) * (
                            Decimal(str(1)) + (Decimal(str(chg_val))) / Decimal(str(100))):
                        break
                elif Decimal(str(chg_val)) < 0:
                    if Decimal(str(rtn_price)) <= Decimal(str(st_price)) * (
                            Decimal(str(1)) + (Decimal(str(chg_val))) / Decimal(str(100))):
                        break
 
        return rtn_price
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_accounts
# - Desc : 잔고정보 조회
# - Input
#   1) except_yn : KRW 및 소액 제외
#   2) market_code : 마켓코드 추가(매도시 필요)
# - Output
#   1) 잔고 정보
# -----------------------------------------------------------------------------
# 계좌 조회
def get_accounts(except_yn, market_code):
    try:
 
        rtn_data = []
 
        # 해당 마켓에 존재하는 종목 리스트만 추출
        market_item_list = get_items(market_code, '')
 
        # 소액 제외 기준
        min_price = 5000
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("GET", server_url + "/v1/accounts", "", headers)
        account_data = res.json()
 
        for account_data_for in account_data:            
            for market_item_list_for in market_item_list:
                
                # 해당 마켓에 있는 종목만 조합
                if market_code + '-' + account_data_for['currency'] == market_item_list_for['market']:
                    
                    # KRW 및 소액 제외
                    if except_yn == "Y" or except_yn == "y":
                        if account_data_for['currency'] != "KRW" and Decimal(str(account_data_for['avg_buy_price'])) * (
                                Decimal(str(account_data_for['balance'])) + Decimal(
                                str(account_data_for['locked']))) >= Decimal(str(min_price)):
                            rtn_data.append(
                                {'market': market_code + '-' + account_data_for['currency'],
                                 'balance': account_data_for['balance'],
                                 'locked': account_data_for['locked'],
                                 'avg_buy_price': account_data_for['avg_buy_price'],
                                 'avg_buy_price_modified': account_data_for['avg_buy_price_modified']})
                    else:
                        if account_data_for['currency'] != "KRW":
                            rtn_data.append(
                            {'market': market_code + '-' + account_data_for['currency'], 'balance': account_data_for['balance'],
                             'locked': account_data_for['locked'],
                             'avg_buy_price': account_data_for['avg_buy_price'],
                             'avg_buy_price_modified': account_data_for['avg_buy_price_modified']})
 
        return rtn_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

    
# -----------------------------------------------------------------------------
# - Name : get_order
# - Desc : 미체결 주문 조회
# - Input
#   1) target_item : 대상종목
# - Output
#   1) 미체결 주문 내역
# -----------------------------------------------------------------------------
def get_order(target_item):
    try:
        query = {
            'market': target_item,
            'state': 'wait',
        }
 
        query_string = urlencode(query).encode()
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("GET", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()
 
        return rtn_data
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : buycoin_tg
# - Desc : 지정가 매수
# - Input
#   1) target_item : 대상종목
#   2) buy_amount : 매수금액
#   3) buy_price : 매수가격
# - Output
#   1) rtn_data : 매수요청결과
# -----------------------------------------------------------------------------
def buycoin_tg(target_item, buy_amount, buy_price):
    try:
 
        # 매수수량 계산
        vol = Decimal(str(buy_amount)) / Decimal(str(buy_price))
 
        query = {
            'market': target_item,
            'side': 'bid',
            'volume': vol,
            'price': buy_price,
            'ord_type': 'limit',
        }
 
        query_string = urlencode(query).encode()
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("POST", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()
 
        logging.info("")
        logging.info("----------------------------------------------")
        logging.info("지정가 매수요청 완료!")
        logging.info(rtn_data)
        logging.info("----------------------------------------------")
 
        return rtn_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise


# -----------------------------------------------------------------------------
# - Name : get_candle
# - Desc : 캔들 조회
# - Input
#   1) target_item : 대상 종목
#   2) tick_kind : 캔들 종류 (1, 3, 5, 10, 15, 30, 60, 240 - 분, D-일, W-주, M-월)
#   3) inq_range : 조회 범위
# - Output
#   1) 캔들 정보 배열
# -----------------------------------------------------------------------------
def get_candle(target_item, tick_kind, inq_range):
    try:
 
        # ----------------------------------------
        # Tick 별 호출 URL 설정
        # ----------------------------------------
        # 분붕
        if tick_kind == "1" or tick_kind == "3" or tick_kind == "5" or tick_kind == "10" or tick_kind == "15" or tick_kind == "30" or tick_kind == "60" or tick_kind == "240":
            target_url = "minutes/" + tick_kind
        # 일봉
        elif tick_kind == "D":
            target_url = "days"
        # 주봉
        elif tick_kind == "W":
            target_url = "weeks"
        # 월봉
        elif tick_kind == "M":
            target_url = "months"
        # 잘못된 입력
        else:
            raise Exception("잘못된 틱 종류:" + str(tick_kind))
 
        logging.debug(target_url)
 
        # ----------------------------------------
        # Tick 조회
        # ----------------------------------------
        querystring = {"market": target_item, "count": inq_range}
        res = send_request("GET", server_url + "/v1/candles/" + target_url, querystring, "")
        candle_data = res.json()
 
        logging.debug(candle_data)
 
        return candle_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

def get_rsi(candle_datas):
    try:
 
        # RSI 데이터 리턴용
        rsi_data = []
 
        # 캔들 데이터만큼 수행
        for candle_data_for in candle_datas:
 
            df = pd.DataFrame(candle_data_for)
            dfDt = df['candle_date_time_kst'].iloc[::-1]
            df = df.reindex(index=df.index[::-1]).reset_index()
 
            df['close'] = df["trade_price"]
 
            # RSI 계산
            def rsi(ohlc: pd.DataFrame, period: int = 14):
                ohlc["close"] = ohlc["close"]
                delta = ohlc["close"].diff()
 
                up, down = delta.copy(), delta.copy()
                up[up < 0] = 0
                down[down > 0] = 0
 
                _gain = up.ewm(com=(period - 1), min_periods=period).mean()
                _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
 
                RS = _gain / _loss
                return pd.Series(100 - (100 / (1 + RS)), name="RSI")
 
            rsi = round(rsi(df, 14).iloc[-1], 4)
            rsi_data.append({"type": "RSI", "DT": dfDt[0], "RSI": rsi})
 
        return rsi_data
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise
 


# -----------------------------------------------------------------------------
# - Name : get_mfi
# - Desc : MFI 조회
# - Input
#   1) candle_datas : 캔들 정보
# - Output
#   1) MFI 값
# -----------------------------------------------------------------------------
def get_mfi(candle_datas):
    try:
 
        # MFI 데이터 리턴용
        mfi_list = []
 
        # 캔들 데이터만큼 수행
        for candle_data_for in candle_datas:
 
            df = pd.DataFrame(candle_data_for)
            dfDt = df['candle_date_time_kst'].iloc[::-1]
 
            df['typical_price'] = (df['trade_price'] + df['high_price'] + df['low_price']) / 3
            df['money_flow'] = df['typical_price'] * df['candle_acc_trade_volume']
 
            positive_mf = 0
            negative_mf = 0
 
            for i in range(0, 14):
 
                if df["typical_price"][i] > df["typical_price"][i + 1]:
                    positive_mf = positive_mf + df["money_flow"][i]
                elif df["typical_price"][i] < df["typical_price"][i + 1]:
                    negative_mf = negative_mf + df["money_flow"][i]
 
            if negative_mf > 0:
                mfi = 100 - (100 / (1 + (positive_mf / negative_mf)))
            else:
                mfi = 100 - (100 / (1 + (positive_mf)))
 
            mfi_list.append({"type": "MFI", "DT": dfDt[0], "MFI": round(mfi, 4)})
 
        return mfi_list
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_macd
# - Desc : MACD 조회
# - Input
#   1) candle_datas : 캔들 정보
#   2) loop_cnt : 반복 횟수
# - Output
#   1) MACD 값
# -----------------------------------------------------------------------------
def get_macd(candle_datas, loop_cnt):
    try:
 
        # MACD 데이터 리턴용
        macd_list = []
 
        df = pd.DataFrame(candle_datas[0])
        df = df.iloc[::-1]
        df = df['trade_price']
 
        # MACD 계산
        exp1 = df.ewm(span=12, adjust=False).mean()
        exp2 = df.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        exp3 = macd.ewm(span=9, adjust=False).mean()
 
        for i in range(0, int(loop_cnt)):
            macd_list.append(
                {"type": "MACD", "DT": candle_datas[0][i]['candle_date_time_kst'], "MACD": round(macd[i], 4),
                 "SIGNAL": round(exp3[i], 4),
                 "OCL": round(macd[i] - exp3[i], 4)})
 
        return macd_list
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise
 
# -----------------------------------------------------------------------------
# - Name : get_bb
# - Desc : 볼린저밴드 조회
# - Input
#   1) candle_datas : 캔들 정보
# - Output
#   1) 볼린저 밴드 값
# -----------------------------------------------------------------------------
def get_bb(candle_datas):
    try:
 
        # 볼린저밴드 데이터 리턴용
        bb_list = []
 
        # 캔들 데이터만큼 수행
        for candle_data_for in candle_datas:
            df = pd.DataFrame(candle_data_for)
            dfDt = df['candle_date_time_kst'].iloc[::-1]
            df = df['trade_price'].iloc[::-1]
 
            # 표준편차(곱)
            unit = 2 # ! 블린저 밴드 표준편차
 
            band1 = unit * numpy.std(df[len(df) - 20:len(df)])
            bb_center = numpy.mean(df[len(df) - 20:len(df)])
            band_high = bb_center + band1
            band_low = bb_center - band1
 
            bb_list.append({"type": "BB", "DT": dfDt[0], "BBH": round(band_high, 4), "BBM": round(bb_center, 4),
                            "BBL": round(band_low, 4)})
 
        return bb_list
 
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_williams
# - Desc : 윌리암스 %R 조회
# - Input
#   1) candle_datas : 캔들 정보
# - Output
#   1) 윌리암스 %R 값
# -----------------------------------------------------------------------------
def get_williams(candle_datas):
    try:
 
        # 윌리암스R 데이터 리턴용
        williams_list = []
 
        # 캔들 데이터만큼 수행
        for candle_data_for in candle_datas:
            df = pd.DataFrame(candle_data_for)
            dfDt = df['candle_date_time_kst'].iloc[::-1]
            df = df.iloc[:14]
 
            # 계산식
            # %R = (Highest High - Close)/(Highest High - Lowest Low) * -100
            hh = numpy.max(df['high_price'])
            ll = numpy.min(df['low_price'])
            cp = df['trade_price'][0]
 
            w = (hh - cp) / (hh - ll) * -100
 
            williams_list.append(
                {"type": "WILLIAMS", "DT": dfDt[0], "HH": round(hh, 4), "LL": round(ll, 4), "CP": round(cp, 4),
                 "W": round(w, 4)})
 
        return williams_list
 
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_indicators
# - Desc : 보조지표 조회
# - Input
#   1) target_item : 대상 종목
#   2) tick_kind : 캔들 종류 (1, 3, 5, 10, 15, 30, 60, 240 - 분, D-일, W-주, M-월)
#   3) inq_range : 캔들 조회 범위
#   4) loop_cnt : 지표 반복계산 횟수
# - Output
#   1) RSI
#   2) MFI
#   3) MACD
#   4) BB
# -----------------------------------------------------------------------------
def get_indicators(target_item, tick_kind, inq_range, loop_cnt):
    try:
 
        # 보조지표 리턴용
        indicator_data = []
 
        # 캔들 데이터 조회용
        candle_datas = []
 
        # 캔들 추출
        candle_data = get_candle(target_item, tick_kind, inq_range)

        if len(candle_data) >= 30: 
            # 조회 횟수별 candle 데이터 조합
            for i in range(0, int(loop_cnt)):
                candle_datas.append(candle_data[i:int(len(candle_data))])

 
 
        # RSI 정보 조회
        rsi_data = get_rsi(candle_datas)
 
        # MFI 정보 조회
        mfi_data = get_mfi(candle_datas)
 
        # MACD 정보 조회
        macd_data = get_macd(candle_datas, loop_cnt)
 
        # BB 정보 조회
        bb_data = get_bb(candle_datas)

        williams_data = get_williams(candle_datas)
 
        if len(rsi_data) > 0:
            indicator_data.append(rsi_data)
 
        if len(mfi_data) > 0:
            indicator_data.append(mfi_data)
 
        if len(macd_data) > 0:
            indicator_data.append(macd_data)
 
        if len(bb_data) > 0:
            indicator_data.append(bb_data)

        if len(williams_data) > 0:
            indicator_data.append(williams_data)
 
        return indicator_data
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise


 
# -----------------------------------------------------------------------------
# - Name : filter_dict
# - Desc : 딕셔너리 필터링
# - Input
#   1) target_dict : 정렬 대상 딕셔너리
#   2) target_column : 정렬 대상 컬럼
#   3) filter : 필터
# - Output
#   1) 필터링된 딕서너리
# -----------------------------------------------------------------------------
def filter_dict(target_dict, target_column, filter):
    try:
 
        for target_dict_for in target_dict[:]:
            if target_dict_for[target_column] != filter:
                target_dict.remove(target_dict_for)
 
        return target_dict
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise


# -----------------------------------------------------------------------------
# - Name : orderby_dict
# - Desc : 딕셔너리 정렬
# - Input
#   1) target_dict : 정렬 대상 딕셔너리
#   2) target_column : 정렬 대상 딕셔너리
#   3) order_by : 정렬방식(False:오름차순, True,내림차순)
# - Output
#   1) 정렬된 딕서너리
# -----------------------------------------------------------------------------
def orderby_dict(target_dict, target_column, order_by):
    try:
 
        rtn_dict = sorted(target_dict, key=(lambda x: x[target_column]), reverse=order_by)
 
        return rtn_dict
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : get_order_status
# - Desc : 주문 조회(상태별)
# - Input
#   1) target_item : 대상종목
#   2) status : 주문상태(wait : 체결 대기, watch : 예약주문 대기, done : 전체 체결 완료, cancel : 주문 취소)
# - Output
#   1) 주문 내역
# -----------------------------------------------------------------------------
def get_order_status(target_item, status):
    try:
 
        query = {
            'market': target_item,
            'state': status,
        }
 
        query_string = urlencode(query).encode()
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("GET", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()
 
        return rtn_data
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise
       
# -----------------------------------------------------------------------------
# - Name : chg_account_to_comma
# - Desc : 잔고 종목 리스트를 콤마리스트로 변경
# - Input
#   1) account_data : 잔고 데이터
# - Output
#   1) 종목 리스트(콤마 구분자)
# -----------------------------------------------------------------------------
def chg_account_to_comma(account_data):
    # ? 이 함수는 왜 있는 거지 --> 안 쓰이는 것 같은데 --> sell_buy에서 쓰임
    try:
 
        rtn_data = ""
 
        for account_data_for in account_data:
 
            if rtn_data == '':
                rtn_data = rtn_data + account_data_for['market']
            else:
                rtn_data = rtn_data + ',' + account_data_for['market']
 
        return rtn_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise
 

def get_ticker(target_itemlist):
    #? 이 함수도 언제 쓰는 거지 --> sell_coin에서 쓰임
    try:
 
        url = "https://api.upbit.com/v1/ticker"
 
        querystring = {"markets": target_itemlist}
        response = send_request("GET", url, querystring, "")
        rtn_data = response.json()
 
        return rtn_data
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise


# ! 아래 함수들 안 쓰이는 것 같음
# ! 

 



#! 아래 함수들은 바뀐 것 같다
# -----------------------------------------------------------------------------
# - Name : get_rsi
# - Desc : RSI 조회
# - Input
#   1) target_item : 대상 종목
#   2) tick_kind : 캔들 종류 (1, 3, 5, 10, 15, 30, 60, 240 - 분, D-일, W-주, M-월)
#   3) inq_range : 조회 범위
# - Output
#   1) RSI 값
# -----------------------------------------------------------------------------
# def get_rsi(target_item, tick_kind, inq_range): 
#     try:
 
#         # 캔들 추출
#         candle_data = get_candle(target_item, tick_kind, inq_range)
 
#         df = pd.DataFrame(candle_data)
#         df = df.reindex(index=df.index[::-1]).reset_index()
 
#         df['close'] = df["trade_price"]
 
#         # RSI 계산
#         def rsi(ohlc: pd.DataFrame, period: int = 14):
#             ohlc["close"] = ohlc["close"]
#             delta = ohlc["close"].diff()
 
#             up, down = delta.copy(), delta.copy()
#             up[up < 0] = 0
#             down[down > 0] = 0
 
#             _gain = up.ewm(com=(period - 1), min_periods=period).mean()
#             _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
 
#             RS = _gain / _loss
#             return pd.Series(100 - (100 / (1 + RS)), name="RSI")
 
#         rsi = round(rsi(df, 14).iloc[-1], 4)
 
#         return rsi
 
 
#     # ----------------------------------------
#     # 모든 함수의 공통 부분(Exception 처리)
#     # ----------------------------------------
#     except Exception:
#         raise

# -----------------------------------------------------------------------------
# - Name : get_williamsR
# - Desc : 윌리암스 %R 조회
# - Input
#   1) target_item : 대상 종목
#   2) tick_kind : 캔들 종류 (1, 3, 5, 10, 15, 30, 60, 240 - 분, D-일, W-주, M-월)
#   3) inq_range : 캔들 조회 범위
#   4) loop_cnt : 지표 반복계산 횟수
# - Output
#   1) 윌리암스 %R 값
# -----------------------------------------------------------------------------
# def get_williamsR(target_item, tick_kind, inq_range, loop_cnt):
#     try:
 
#         # 캔들 데이터 조회용
#         candle_datas = []
 
#         # 윌리암스R 데이터 리턴용
#         williams_list = []
 
#         # 캔들 추출
#         candle_data = get_candle(target_item, tick_kind, inq_range)
 
#         # 조회 횟수별 candle 데이터 조합
#         for i in range(0, int(loop_cnt)):
#             candle_datas.append(candle_data[i:int(len(candle_data))])
 
#         # 캔들 데이터만큼 수행
#         for candle_data_for in candle_datas:
 
#             df = pd.DataFrame(candle_data_for)
#             dfDt = df['candle_date_time_kst'].iloc[::-1]
#             df = df.iloc[:14]
 
#             # 계산식
#             # %R = (Highest High - Close)/(Highest High - Lowest Low) * -100
#             hh = numpy.max(df['high_price'])
#             ll = numpy.min(df['low_price'])
#             cp = df['trade_price'][0]
 
#             w = (hh - cp)/(hh - ll) * -100
 
#             williams_list.append({"type": "WILLIAMS", "DT": dfDt[0], "HH": round(hh, 4), "LL": round(ll, 4), "CP": round(cp, 4), "W": round(w, 4)})
 
#         return williams_list
 
 
#     # ----------------------------------------
#     # 모든 함수의 공통 부분(Exception 처리)
#     # ----------------------------------------
#     except Exception:
#         raise

# -----------------------------------------------------------------------------
# - Name : get_bb
# - Desc : 볼린저밴드 조회
# - Input
#   1) target_item : 대상 종목
#   2) tick_kind : 캔들 종류 (1, 3, 5, 10, 15, 30, 60, 240 - 분, D-일, W-주, M-월)
#   3) inq_range : 캔들 조회 범위
#   4) loop_cnt : 지표 반복계산 횟수
# - Output
#   1) 볼린저 밴드 값
# -----------------------------------------------------------------------------
# def get_bb(target_item, tick_kind, inq_range, loop_cnt):
#     try:
 
#         # 캔들 데이터 조회용
#         candle_datas = []
 
#         # 볼린저밴드 데이터 리턴용
#         bb_list = []
 
#         # 캔들 추출
#         candle_data = get_candle(target_item, tick_kind, inq_range)
 
#         # 조회 횟수별 candle 데이터 조합
#         for i in range(0, int(loop_cnt)):
#             candle_datas.append(candle_data[i:int(len(candle_data))])
 
#         # 캔들 데이터만큼 수행
#         for candle_data_for in candle_datas:
#             df = pd.DataFrame(candle_data_for)
#             dfDt = df['candle_date_time_kst'].iloc[::-1]
#             df = df['trade_price'].iloc[::-1]
 
#             # 표준편차(곱)
#             unit = 2 
 
#             band1 = unit * numpy.std(df[len(df) - 20:len(df)])
#             bb_center = numpy.mean(df[len(df) - 20:len(df)])
#             band_high = bb_center + band1
#             band_low = bb_center - band1
 
#             bb_list.append({"type": "BB", "DT": dfDt[0], "BBH": round(band_high, 4), "BBM": round(bb_center, 4),
#                            "BBL": round(band_low, 4)})
 
#         return bb_list
 
 
#     # ----------------------------------------
#     # 모든 함수의 공통 부분(Exception 처리)
#     # ----------------------------------------
#     except Exception:
#         raise

# -----------------------------------------------------------------------------
# - Name : get_macd
# - Desc : MACD 조회
# - Input
#   1) target_item : 대상 종목
#   2) tick_kind : 캔들 종류 (1, 3, 5, 10, 15, 30, 60, 240 - 분, D-일, W-주, M-월)
#   3) inq_range : 캔들 조회 범위
#   4) loop_cnt : 지표 반복계산 횟수
# - Output
#   1) MACD 값
# # -----------------------------------------------------------------------------
# def get_macd(target_item, tick_kind, inq_range, loop_cnt):
#     try:
 
#         # 캔들 데이터 조회용
#         candle_datas = []
 
#         # MACD 데이터 리턴용
#         macd_list = []
 
#         # 캔들 추출
#         candle_data = get_candle(target_item, tick_kind, inq_range)
 
#         # 조회 횟수별 candle 데이터 조합
#         for i in range(0, int(loop_cnt)):
#             candle_datas.append(candle_data[i:int(len(candle_data))])
 
#         df = pd.DataFrame(candle_datas[0])
#         df = df.iloc[::-1]
#         df = df['trade_price']
 
#         # MACD 계산
#         exp1 = df.ewm(span=12, adjust=False).mean()
#         exp2 = df.ewm(span=26, adjust=False).mean()
#         macd = exp1 - exp2
#         exp3 = macd.ewm(span=9, adjust=False).mean()
 
#         for i in range(0, int(loop_cnt)):
#             macd_list.append(
#                 {"type": "MACD", "DT": candle_datas[0][i]['candle_date_time_kst'], "MACD": round(macd[i], 4), "SIGNAL": round(exp3[i], 4),
#                  "OCL": round(macd[i] - exp3[i], 4)})
 
#         return macd_list
 
#     # ----------------------------------------
#     # 모든 함수의 공통 부분(Exception 처리)
#     # ----------------------------------------
#     except Exception:
#         raise

