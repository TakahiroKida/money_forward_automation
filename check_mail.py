import logging
import os
from utils.common_functions import str_2_datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_input_datas(gmail:object, config:object) -> list:
    '''
    対象メールの内容を取得し、加工する
    '''
    result_list = []
    format_price = lambda x: x.replace(',', '').replace('￥', '').replace('\\', '').replace('円', '').replace('JPY', '').strip()
    mail_labels = {k.upper(): v for k, v in config['MAIL_LABEL'].items()}
    pay_method  = {k.upper(): v for k, v in config['PAY_METHOD'].items()}
    for pay, label_id in mail_labels.items():
        mail_list = gmail.get_messages(label_ids=[label_id], limit=5, is_unread=True)
        for mail in mail_list:
            try:
                income = False
                subject = mail.get('Subject')
                if pay == 'AMAZON':
                    ####################################################################################################
                    # AMAZON
                    ####################################################################################################
                    if subject.startswith('注文済み:'):
                        # 通常の注文
                        body = mail.get('body').split('注文番号')[-1].split('合計')[0].strip().split('\n\n')[-1]
                        lines = [line.replace('*', '').strip() for line in body.split('\n')]
                        buy_date = str_2_datetime(mail.get('Date').replace(' (JST)', ''), '%a, %d %b %Y %H:%M:%S %z')
                        date = f'{buy_date.year}/{str(buy_date.month).zfill(2)}/{str(buy_date.day).zfill(2)}'
                        price = int(int(lines[1].replace('数量: ', '')) * int(format_price(lines[2])))
                        description = lines[0][:50]
                        if description == 'Amazonギフトカード チャージタイプ': continue
                    elif subject.startswith('Amazon.co.jpでのご注文:') or subject.endswith('Amazon.co.jpのご注文。'):
                        # Kindle
                        body = mail.get('body').split('注文番号:')[-1].split('*表示される合計金額は')[0].strip()
                        lines = [line.replace('*', '').strip() for line in body.split('\n') if line]
                        buy_date = lines[0].split('注文日: ')[-1].split('日')[0].replace('年', '/').replace('月', '/')
                        year, month, day = buy_date.split('/')
                        date = f'{year}/{month.zfill(2)}/{day.zfill(2)}'
                        price = format_price(lines[-1].replace('総計:', ''))
                        description = '書籍'
                    else:
                        # AMAZON_PAY
                        body = mail.get('body').split('お取引の概要')[-1].split('ご利用の詳細を確認する')[0].strip()
                        tmp_dict = {split_line[0].strip(): split_line[1].strip() for line in body.split('\n') if len((split_line:=line.split(' ', 1)))==2}
                        if tmp_dict.get('お支払い方法', '')!='Amazonギフトカード': continue
                        buy_date = tmp_dict.get('処理日', '').split('日')[0].replace('年', '/').replace('月', '/')
                        year, month, day = buy_date.split('/')
                        date = f'{year}/{month.zfill(2)}/{day.zfill(2)}'
                        price = format_price(tmp_dict.get('ご請求金額', ''))
                        description = tmp_dict.get('販売事業者お問い合わせ先', '').split('   ')[0][:50]

                elif pay == 'ANA':
                    ####################################################################################################
                    # ANA
                    ####################################################################################################
                    if subject.startswith('［ANA Pay］ご利用のお知らせ'):
                        # 通常の注文
                        lines = [line for line in mail.get('body').split('\n') if '：' in line]
                        tmp_dict = {split_line[0]: split_line[1] for line in lines if len((split_line:=line.split('：')))==2}
                        if not tmp_dict: continue
                        date = tmp_dict.get('ご利用日時', '').split(' ')[0].replace('-', '/')
                        price = format_price(tmp_dict.get('ご利用金額', ''))
                        description = tmp_dict.get('ご利用店舗', '').strip()[:50]
                    elif subject.startswith('［ANA Pay］マイルからのチャージ完了のお知らせ'):
                        # マイルチャージ
                        lines = [line for line in mail.get('body').split('\n') if '：' in line]
                        tmp_dict = {split_line[0]: split_line[1] for line in lines if len((split_line:=line.split('：')))==2}
                        if not tmp_dict: continue
                        buy_date = str_2_datetime(mail.get('Date').replace(' (JST)', ''), '%a, %d %b %Y %H:%M:%S %z')
                        date = f'{buy_date.year}/{str(buy_date.month).zfill(2)}/{str(buy_date.day).zfill(2)}'
                        price = format_price(tmp_dict.get('チャージマイル数', '').replace('マイル', ''))
                        description = 'ANAマイル利用'
                        income = True

                elif pay == 'RAKUTEN_PAY':
                    ####################################################################################################
                    # 楽天Pay
                    ####################################################################################################
                    body = mail.get('body').split('ご利用明細')[-1].split('獲得予定ポイント')[0].strip()
                    lines = [line.strip() for line in body.split('\n')]
                    tmp_dict = {
                        split_line[0].strip(): split_line[1].strip() for line in lines
                        if len((split_line:=line.split(maxsplit=1)))==2
                    }
                    date = tmp_dict.get('ご利用日時', '').split('(')[0]
                    price = format_price(tmp_dict.get('決済総額', ''))
                    description = tmp_dict.get('ご利用店舗', '').strip()[:50]
                
                ####################################################################################################
                # 共通処理
                ####################################################################################################
                if price == '0': continue
                input_data = {
                    'pay'        : pay if pay in pay_method else '', 
                    'date'       : date,
                    'price'      : price,
                    'description': description,
                    'income'     : income,
                }
                result_list.append(input_data)
                gmail.change_read_state(mail.get('id'))
            except Exception as e:
                logger.error(f'メール内容解析: 失敗\n{e}')
    return result_list
