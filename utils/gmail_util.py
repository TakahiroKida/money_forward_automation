# 参考サイト
# https://sqripts.com/2022/08/25/20386/
# requirements
# pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib filetype
import base64
import filetype
import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from io import BytesIO
from typing import Union, List

class Gmail_Util():
    ####################################################################################################
    # プロパティ
    ####################################################################################################
    # GmailのAPI
    __SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    ####################################################################################################
    # コンストラクタ
    ####################################################################################################
    def __init__(self, credentials_path:str='', token_path:str=''):
        # 認証JSONもトークンもない場合はエラー
        if not any([credentials_path, token_path]):
            raise Exception('認証JSONかトークンは必須です')
        # 認証オブジェクト
        self._creds = None
        # 属性に代入
        self._credentials_path = credentials_path
        # 認証フローが初めて完了したときに自動的にtoken.jsonが作成されます
        self._token_path = token_path or './token.json'
        if token_path and os.path.exists(token_path):
            self.set_token(token_path)
        # 有効期限チェック
        self.refresh_token()
        # APIサービスを扱うオブジェクト
        self._service = build('gmail', 'v1', credentials=self._creds)
        # ユーザ情報
        self._profile = self._service.users().getProfile(userId='me').execute()

    ####################################################################################################
    # ゲッター
    ####################################################################################################
    @property
    def credentials(self):
        return self._creds

    @property
    def service(self):
        return self._service

    @property
    def profile(self):
        return self._profile

    @property
    def labels(self) -> dict:
        labels = self._service.users().labels().list(userId='me').execute()
        return labels.get('labels')

    ####################################################################################################
    # メソッド
    ####################################################################################################
    def refresh_token(self, update_token_file:bool=True):
        '''
        トークンの有効期限を確認する
        有効期限が切れていればリフレッシュ
        '''
        if self._creds and self._creds.expired and self._creds.refresh_token:
            # 有効期限切れの場合
            self._creds.refresh(Request())
        elif self._creds and self._creds.refresh_token:
            # 問題ない場合
            return self._creds
        else:
            # なんもない場合
            flow = InstalledAppFlow.from_client_secrets_file(self._credentials_path, self.__SCOPES)
            self._creds = flow.run_local_server(port=0)
        # 新しい認証情報をtoken.jsonに保存します。
        if update_token_file:
            with open(self._token_path, 'w') as token:
                token.write(self._creds.to_json())
        return self._creds
    
    def set_token(self, token_path:str):
        '''
        トークンセット
        '''
        self._token_path = os.path.abspath(token_path)
        self._creds = Credentials.from_authorized_user_file(self._token_path, self.__SCOPES)
        self.refresh_token()
    
    def get_messages(self, label_ids:list[str]=None, limit:int=3, is_unread:bool=False) -> list:
        '''
        メールボックスの内容取得
        '''
        self.refresh_token()
        label_ids = list(label_ids) if label_ids is not None else ['INBOX']
        params = {
            'userId'    : 'me',
            'labelIds'  : label_ids,
            'maxResults': limit,
        }
        if is_unread: params['q'] = 'is:unread'
        mail_datas = self._service.users().messages().list(**params).execute()
        messages = mail_datas.get('messages', [])
        datas = [
            self._service.users().messages().get(userId='me', id=message.get('id')).execute()
            for message in messages
        ]
        result_list = [
            self.format_mail_info(data)
            for data in datas
            if not is_unread or ('UNREAD' in data.get('labelIds', []))
        ]
        return result_list

    def format_mail_info(self, mail_data:dict) -> dict:
        '''
        情報整形
        '''
        tgt_key = ['Date', 'Subject', 'From', 'To']
        result_dict = {
            tmp.get('name'): tmp.get('value')
            for tmp in mail_data['payload']['headers']
            if tmp.get('name') in tgt_key
        }
        result_dict['id']   = mail_data.get('id', '')
        payload = mail_data.get('payload', {})
        mail_body = parts[0].get('body', {}) if (parts:=payload.get('parts')) else payload.get('body', {})
        result_dict['body'] = base64.urlsafe_b64decode(mail_body.get('data', '')).decode('utf-8')
        result_dict['label_ids'] = mail_data.get('labelIds', [])
        return result_dict
    
    def change_read_state(self, message_id:str, mark_as_read:bool=True):
        '''
        メールの既読・未読切り替える
        mark_as_read=True  → 既読にする
        mark_as_read=False → 未読にする
        '''
        body = {}
        if mark_as_read:
            body['removeLabelIds'] = ['UNREAD']
        else:
            body['addLabelIds'] = ['UNREAD']
        self._service.users().messages().modify(
            userId='me',
            id=message_id,
            body=body
        ).execute()
    
    def create_mail(
        self, to:Union[str, List[str]], cc:Union[str, List[str]]='', bcc:Union[str, List[str]]='',
        subject:str='', body:str='', attachment_files:List[Union[str, bytes, BytesIO]]=[]
    ) -> dict:
        '''
        メール作成
        '''
        # 配列の場合文字に変換
        def list_to_str(tgt):
            if isinstance(tgt, list):
                tgt = ','.join(tgt)
            return tgt
        mail_data = MIMEMultipart()
        # 送信先
        mail_data['to'] = list_to_str(to)
        # 件名
        mail_data['subject'] = subject
        # CC,BCCがある場合
        if cc:
            mail_data['cc'] = list_to_str(cc)
        if bcc:
            mail_data['bcc'] = list_to_str(bcc)
        # メールの送受信先、件名本文内容追加
        # 本文をメールテキストに
        message = MIMEText(body)
        mail_data.attach(message)
        # 添付ファイル情報があれば追加
        if attachment_files:
            for i, attachment_file in enumerate(attachment_files, start=1):
                mime_base = MIMEBase('application', 'octet-stream')
                if isinstance(attachment_file, str):
                    file_path = os.path.abspath(attachment_file)
                    file_name = os.path.basename(attachment_file)
                    with open(file_path, 'rb') as f:
                        mime_base.set_payload(f.read())
                elif isinstance(attachment_file, BytesIO):
                    attachment_file.seek(0)
                    mime_base.set_payload(attachment_file.read())
                    if hasattr(attachment_file, 'name'):
                        file_name = attachment_file.name
                    else:
                        attachment_file.seek(0)
                        extention = guess.extension if (guess:=filetype.guess(attachment_file)) else 'txt'
                        file_name = f'attachment{i}.{extention}'
                elif isinstance(attachment_file, bytes):
                    mime_base.set_payload(attachment_file)
                    extention = guess.extension if (guess:=filetype.guess(attachment_file)) else 'txt'
                    file_name = f'attachment{i}.{extention}'
                else:
                    continue
                # エンコード
                encoders.encode_base64(mime_base)
                # ヘッダー設定
                mime_base.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
                # メールに追加
                mail_data.attach(mime_base)
        # Base64に変換 
        raw = base64.urlsafe_b64encode(mail_data.as_bytes()).decode()
        return {'raw': raw}
    
    def send_mail(self, mail_data:dict, user_id:str='me'):
        '''
        メール送信
        '''
        self.refresh_token()
        message = self._service.users().messages().send(userId=user_id, body=mail_data).execute()
        return message

if __name__ == '__main__':
    # credentials_path = './credentials.json'
    token_path = '../token.json'
    gmail_util = Gmail_Util(token_path=token_path)
    gmail_util.labels
    tmp = gmail_util.get_messages(label_ids=['Label_8488675827904555725'], limit=1, is_unread=True)
    # mail = gmail_util.create_mail(to='kida-ta@dym.jp', cc='takahiro.kida.job@gmail.com', subject='TEST', body='テスト送信\n\n改行のてすとも', attachment_files=['./test.txt'])
    # gmail_util.send_mail(mail_data=mail)

    import pdb;pdb.set_trace()