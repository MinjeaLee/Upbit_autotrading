import os
import time
import math
import sys
import logging
import traceback

from decimal import Decimal
 
# ���� ��� Import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from module import upbit as upbit  # noqa

# -----------------------------------------------------------------------------
# - Name : start_selltrade
# - Desc : �ŵ� ����
# - Input
# 1) target_item : ��� ����
# 2) rsi_sell_value : �ŵ� ���� RSI ��
# 3) rsi_buy_value : �ż� ���� RSI ��
# 4) buy_amt : �ż� �ݾ�
# -----------------------------------------------------------------------------
def start_selltrade(target_item, rsi_sell_valuel, rsi_buy_value, buy_amt):
    try:
 
        # �ŵ� �ɶ����� �ݺ�
        while True:
 
            logging.info('�ŵ� ���� ������...')
 
            # �ش� ������ RSI ��ǥ ����
            # 1. 10�к� ���� RSI ��ǥ ����
            rsi_data = upbit.get_indicators(target_item, '10', 200, 5)
 
            # RSI ���� ���ذ��� �ʰ��ϸ� �ŵ�
            if Decimal(rsi_data[0][0]['RSI']) > Decimal(rsi_sell_value):
 
                # ���� ���� ���� RSI ������
                logging.info(rsi_data)
 
                # ���尡 �ŵ�
                logging.info('���尡 �ŵ� ����!')
                #upbit.sellcoin_mp(target_item, 'Y')
 
                # �ŵ� �ð� ó�� ���
                time.sleep(3)
 
                # �ٽ� �ż� ���� ����
                start_buytrade(rsi_buy_value, rsi_sell_value, buy_amt)
 
    # ----------------------------------------
    # ��� �Լ��� ���� �κ�(Exception ó��)
    # ----------------------------------------
    except Exception:
        raise
 
 
# -----------------------------------------------------------------------------
# - Name : start_buytrade
# - Desc : �ż� ����
# - Input
# 1) rsi_buy_value : �ż� ���� RSI ��
# 2) rsi_sell_value : �ŵ� ���� RSI ��
# 3) buy_amt : �ż��ݾ�
# -----------------------------------------------------------------------------
def start_buytrade(rsi_buy_value, rsi_sell_value, buy_amt):
    try:
 
        data_cnt = 0
 
        # �ż� �� ������ �ݺ� ����
        while True:
 
            # ��ü ���� ����
            # 1. KRW����
            # 2. BTC, ETH ����
            item_list = upbit.get_items('KRW', 'BTC,ETH')
 
            # ��ü ���� �ݺ�
            for item_list_for in item_list:
 
                # �ش� ������ RSI ��ǥ ����
                # 1. 10�к� ���� RSI ��ǥ ����
                rsi_data = upbit.get_indicators(item_list_for['market'], '10', 200, 5)
 
                # RSI ���� ���ذ� �̸����� �������� �ż�
                if Decimal(rsi_data[0][0]['RSI']) < Decimal(rsi_buy_value):
 
                    # ���� ���� ���� �α�
                    logging.info(item_list_for)
 
                    # ���� ���� ���� RSI ������
                    logging.info(rsi_data)
 
                    # ���尡 �ż�
                    logging.info('���尡 �ż� ����!')
                    #upbit.buycoin_mp(item_list_for['market'], buy_amt)
 
                    # �ż� �ð� ó�� ���
                    time.sleep(3)
 
                    # �ŵ� ���� ȣ��
                    start_selltrade(item_list_for['market'], rsi_sell_value, rsi_buy_value, buy_amt)
 
                if data_cnt == 0 or data_cnt % 100 == 0:
                    logging.info("�ż� ���� ������...[" + str(data_cnt) + "]")
 
                # ��ȸ�Ǽ�����
                data_cnt = data_cnt + 1
 
    # ----------------------------------------
    # ��� �Լ��� ���� �κ�(Exception ó��)
    # ----------------------------------------
    except Exception:
        raise
 
 
# -----------------------------------------------------------------------------
# - Name : main
# - Desc : ����
# -----------------------------------------------------------------------------
if __name__ == '__main__':
 
    # noinspection PyBroadException
    try:
 
        print("***** USAGE ******")
        print("[1] �α׷���(D:DEBUG, E:ERROR, �׿�:INFO)")
 
        # �α׷���(D:DEBUG, E:ERROR, �׿�:INFO)
        upbit.set_loglevel('I')
 
        # ---------------------------------------------------------------------
        # Logic Start!
        # ---------------------------------------------------------------------
        rsi_buy_value = input("�ż� ���� RSI ��(ex. 30):")
        rsi_sell_value = input("�ŵ� ���� RSI ��(ex. 70):")
        buy_amt = input("�ż��ݾ�(ex:10000):")
 
        logging.info("�ż� ���� RSI ��:" + str(rsi_buy_value))
        logging.info("�ŵ� ���� RSI ��:" + str(rsi_sell_value))
        logging.info("�ż��ݾ�:" + str(buy_amt))
 
        # �ż����� ����
        start_buytrade(rsi_buy_value, rsi_sell_value, buy_amt)
 
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception �߻�!")
        logging.error(traceback.format_exc())
        sys.exit(-100)
 
    except Exception:
        logging.error("Exception �߻�!")
        logging.error(traceback.format_exc())
        sys.exit(-200)