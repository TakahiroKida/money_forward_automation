import logging
import os
import re
import sys
from const import PAY_CATEGORY
from utils.chrome_util import ChromeUtil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_chrome() -> ChromeUtil:
    '''
    chrome起動
    '''
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
    options_list = [
        '--headless=new',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        f'--user-agent={user_agent}',
        '--window-size=1920,1080',
    ]
    chrome = ChromeUtil(
        options_str_list=options_list,
    )
    chrome.driver.maximize_window()
    return chrome

def login(chrome:object, gmail:object, config:object):
    '''
    ログイン
    '''
    try:
        login_id = config.get('MONEY_FORWARD', 'login_id')
        login_pw = config.get('MONEY_FORWARD', 'login_pw')
        chrome.open_url('https://moneyforward.com/login')
        chrome.find_element('class', 'link-btn-reg').js_click()
        chrome.find_element('id', 'mfid_user[email]').send_keys(login_id)
        chrome.find_element('id', 'submitto').js_click()
        logger.info('ログインID入力: 完了')
        chrome.load_wait(sleep_time=1)
        chrome.find_element('id', 'mfid_user[password]').send_keys(login_pw)
        chrome.find_element('id', 'submitto').js_click()
        logger.info('ログインPW入力: 完了')
        # ワンタイムパスワード取得
        onetime_mail_label_id = config.get('MAIL_LABEL', 'onetime_mail_label_id')
        for i in range(1, 11):
            logger.info(f'{i}回目: 5秒待機...')
            chrome.load_wait(sleep_time=5)
            mail_list = gmail.get_messages(label_ids=[onetime_mail_label_id], limit=1, is_unread=True)
            if mail_list: break
        if not mail_list:
            raise Exception('ワンタイムパスワード取得失敗')
        logger.info('ワンタイムパスワード取得: 完了')
        gmail.change_read_state(mail_list[0].get('id'))
        one_time_pw = [line for line in mail_list[0].get('body').split('\n') if re.match('^[0-9]{6}', line.strip())]
        one_time_pw = one_time_pw[0].strip()
        chrome.find_element('id', 'email_otp').send_keys(one_time_pw)
        chrome.find_element('id', 'submitto').js_click()
        logger.info('ワンタイムパスワード入力: 完了')
        chrome.load_wait(sleep_time=1)
        if 'https://moneyforward.com/' != chrome.current_url:
            raise Exception(f'ログイン失敗: {chrome.current_url}')
    except Exception as e:
        import pdb;pdb.set_trace()
    

def input_amount(chrome:object, config:object, input_datas:dict):
    '''
    金額入力
    '''
    pay_method  = {k.upper(): v for k, v in config['PAY_METHOD'].items()}
    input_link = chrome.find_element('css_selector', '.pull-right.more-link').get_attribute('href')
    for i, input_data in enumerate(input_datas, start=1):
        logger.info(f'{i}件目のデータ入力: 開始')
        chrome.location_href(input_link)
        chrome.load_wait(sleep_time=1)
        # 入力タイプ選択
        if input_data.get('income'):
            chrome.find_element('css_selector', '#info input').js_click()
            chrome.load_wait(sleep_time=1)
        # 日付入力
        date_ele = chrome.find_element('id', 'updated-at')
        date_ele.clear()
        date_ele.send_keys(input_data.get('date'))
        chrome.load_wait(sleep_time=1)
        date_ele.click()
        # 金額入力
        price = input_data.get('price')
        chrome.find_element('id', 'appendedPrependedInput').send_keys(price)
        logger.info(f'金額: {price}円')
        # 支出元入力
        if (pay:=input_data.get('pay')):
            tgt_select = chrome.find_element('id', 'user_asset_act_sub_account_id_hash').select
            tgt_select.select_by_value(pay_method.get(pay))
            logger.info(f'支出元: {pay}')
        # PAY_CATEGORY
        description = input_data.get('description')
        if (category:=PAY_CATEGORY.get(description)):
            cate1, cate2 = category
            logger.info(f'カテゴリ: {cate1} → {cate2}')
            chrome.find_element('id', 'js-large-category-selected').js_click()
            chrome.load_wait(sleep_time=1)
            tgt_ele = [ele for ele in chrome.find_elements('class', 'l_c_name') if ele.text==cate1]
            if tgt_ele:
                tgt_ele[0].js_click()
                chrome.find_element('id', 'js-middle-category-selected').js_click()
                chrome.load_wait(sleep_time=1)
                tgt_ele = [ele for ele in chrome.find_elements('class', 'm_c_name') if ele.text==cate2]
                if tgt_ele: tgt_ele[0].js_click()
        # 支出内容
        chrome.find_element('id', 'js-content-field').send_keys(description)
        chrome.find_element('name', 'commit').js_click()
        logger.info(f'支出先: {description}')
        for _ in range(5):
            chrome.load_wait(sleep_time=1)
            alert_ele = chrome.find_element('id', 'alert-area', timeout=1)
            if alert_ele and alert_ele.text=='入力を保存しました。':
                break
        chrome.location_href('https://moneyforward.com/')
        logger.info(f'{i}件目のデータ入力: 完了')