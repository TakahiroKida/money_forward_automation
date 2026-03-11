import logging
import os
import sys
from configparser import ConfigParser
from check_mail import *
from rpa_process import *
from utils.gmail_util import GmailUtil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def main():
    try:
        ####################################################################################################
        # コンフィグ読込
        ####################################################################################################
        now_task = 'Chrome起動'
        logger.info(f'{now_task}: 開始')
        if len(sys.argv) < 2:
            raise Exception('iniファイル名を引数に入れてください')
        config_path = os.path.join('initials', sys.argv[-1])
        config = ConfigParser()
        config.read(config_path, encoding='utf-8')
        logger.info(f'{now_task}: 完了')

        ####################################################################################################
        # メール確認
        ####################################################################################################
        now_task = 'メール確認'
        logger.info(f'{now_task}: 開始')
        token_path = os.path.join('token_files', config.get('GOOGLE', 'token_file'))
        gmail = GmailUtil(token_path=token_path)
        input_datas = get_input_datas(gmail, config)
        logger.info(f'対象: {len(input_datas)}件')
        if not input_datas: return
        logger.info(f'{now_task}: 完了')

        ####################################################################################################
        # Chrome起動
        ####################################################################################################
        now_task = 'Chrome起動'
        logger.info(f'{now_task}: 開始')
        chrome = get_chrome()
        logger.info(f'{now_task}: 完了')

        ####################################################################################################
        # ログイン
        ####################################################################################################
        now_task = 'ログイン'
        logger.info(f'{now_task}: 開始')
        login(chrome, gmail, config)
        logger.info(f'{now_task}: 完了')

        ####################################################################################################
        # 金額入力
        ####################################################################################################
        now_task = '金額入力'
        logger.info(f'{now_task}: 開始')
        input_amount(chrome, config, input_datas)
        logger.info(f'{now_task}: 完了')

    except Exception as e:
        logger.info(f'{now_task}: 失敗\n{e}')
        raise


if __name__ == '__main__':
    main()