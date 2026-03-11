import base64
import logging
import threading
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from typing import Union

logger = logging.getLogger(__name__)

class CustomElement(WebElement):
    '''
    機能を追加したWebElementクラス
    セレニウムのWebElementクラスを継承
    '''
    ####################################################################################################
    # プロパティ
    ####################################################################################################
    # 絵文字インプット用のJS
    __INPUT_EMOJI = '''
        arguments[0].value += arguments[1];
        arguments[0].dispatchEvent(new Event('change'));
    '''

    ####################################################################################################
    # コンストラクタ
    ####################################################################################################
    def __init__(self, driver, element_id:str):
        super().__init__(driver, element_id)
    
    ####################################################################################################
    # ゲッター
    ####################################################################################################
    @property
    def parent_ele(self):
        # 親要素を返却
        return self.find_element('xpath', '..')
    
    @property
    def select(self) -> Select:
        # セレクトボックスのクラスを返却する
        return Select(self.web_element)
        
    @property
    def value(self) -> str:
        return self.get_attribute('value')
    
    @property
    def web_element(self) -> WebElement:
        # アッパーキャストしたWebElement
        return WebElement(self._parent, self.id)

    ####################################################################################################
    # メソッド
    ####################################################################################################
    def set_attribute(self, attribute:str, value:str):
        '''
        エレメントの属性に値をセット
        '''
        self._parent.execute_script(f'arguments[0].{attribute} = arguments[1]', self, value)
    
    def js_click(self):
        '''
        JSを使ってクリック
        '''
        self._parent.execute_script('arguments[0].click();', self)
    
    def scroll(self):
        '''
        このエレメントまでスクロール
        '''
        self._parent.execute_script("arguments[0].scrollIntoView({ behavior: 'auto', block: 'center' });", self.web_element)
    
    def send_keys_js(self, text:str):
        '''
        絵文字を書き込みたいとき用
        '''
        self._parent.execute_script(self.__INPUT_EMOJI, self.web_element, text)
            
    def find_element(self, mode:str, word:str):
        '''
        エレメント検索
        オーバーライドしているので元のを使いたい場合はweb_elementを取得してから実行してください
        '''
        elements = self.find_elements(mode, word, 1) or []
        return elements[0] if len(elements) > 0 else None

    def find_elements(self, mode:str, word:str, max_ele_num:int=-1) -> list:
        '''
        エレメント検索
        オーバーライドしているので元のを使いたい場合はweb_elementを取得してから実行してください
        '''
        tgt_mode = {
            'id'          : By.ID,
            'class'       : By.CLASS_NAME,
            'tag'         : By.TAG_NAME,
            'name'        : By.NAME,
            'xpath'       : By.XPATH,
            'css_selector': By.CSS_SELECTOR,
            'link_text'   : By.LINK_TEXT,
        }.get(mode)
        try:
            ele_list = super().find_elements(tgt_mode, word)
            if max_ele_num != -1:
                ele_list = ele_list[:max_ele_num]
            return [CustomElement(self._parent, ele.id) for ele in ele_list]
        except Exception as e:
            return []


class ChromeUtil:
    ####################################################################################################
    # コンストラクタ
    ####################################################################################################
    def __init__(
        self, driver_path:str=None, options_str_list:list=None,
        experimental_option_dict:dict=None, binary_location:str=None, i_am_human:bool=True,
    ):
        # オプション設定
        options = webdriver.ChromeOptions()
        if binary_location:
            options.binary_location = binary_location
        if options_str_list:
            for option_str in options_str_list:
                options.add_argument(option_str)
        
        # カスタムされたDLパスがある場合
        experimental_option_dict = experimental_option_dict or {}
        self._download_dir = experimental_option_dict.get('prefs', {}).get('download.default_directory') or ''
        # experimentalオプションの追加
        if experimental_option_dict:
            for key, ex_option in experimental_option_dict.items():
                if ex_option is None: continue
                options.add_experimental_option(key, ex_option)
        
        # 極力ロボットであることを隠蔽するオプション
        if i_am_human:
            # Chromeが自動化制御下にあることを示すBlink内部フラグを無効化（AutomationControlledを消す）
            options.add_argument('--disable-blink-features=AutomationControlled')
            # Chrome起動時に付与される「enable-automation」スイッチを除外（自動化痕跡の削減）
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            # Chromeの自動化拡張（Automation Extension）を無効化（自動化関連オブジェクトの削減）
            options.add_experimental_option('useAutomationExtension', False)

        # ChromeDriverの起動
        if driver_path:
            self._driver = webdriver.Chrome(service=Service(executable_path=driver_path), options=options)
        else:
            self._driver = webdriver.Chrome(options=options)
        self.load_wait()
    
    ####################################################################################################
    # ゲッター
    ####################################################################################################
    @property
    def actions(self) -> ActionChains:
        return ActionChains(self._driver)
    
    @property
    def active_element(self):
        # アクティブなエレメント
        return CustomElement(self._driver, self._driver.switch_to.active_element.id)

    @property
    def alert(self):
        try:
            # アラートを取得
            # OK → alert.accept() キャンセル → alert.dismiss()
            return WebDriverWait(self._driver, 1).until(EC.alert_is_present())
        except:
            return None
    
    @property
    def cookies(self) -> list:
        # Cookie取得
        return {c['name']: c['value'] for c in self._driver.get_cookies()}

    @property
    def current_url(self) -> str:
        # 現在のURL取得
        return self._driver.current_url
    
    @property
    def download_dir(self) -> str:
        # ダウンロード先（空白の場合はデフォルトのまま）
        return self._download_dir
    
    @property
    def driver(self):
        # ドライバ取得
        return self._driver

    @property
    def keys(self) -> Keys:
        return Keys
    
    @property
    def tab_id(self) -> str:
        # 現在のTabId
        return self._driver.current_window_handle
    
    @property
    def tab_id_list(self) -> list:
        # TabIdのリスト
        return self._driver.window_handles
    
    @property
    def user_agent(self) -> str:
        # user_agent取得
        user_agent = self._driver.execute_script('return navigator.userAgent;')
        return user_agent
    
    ####################################################################################################
    # メソッド
    ####################################################################################################
    def close_driver(self):
        '''
        ドライバクローズ（非同期）
        daemon=True：メインプログラム終了時にサブスレッドも自動終了します。
        '''
        thread = threading.Thread(target=self._driver.quit, daemon=True)
        thread.start()
        
    def open_url(self, url:str, timeout:int=20) -> bool:
        '''
        URLを開く
        '''
        try:
            # ポップアップ無効
            self._driver.get(url)
            self._driver.execute_script('window.onbeforeunload = function() {};')
            self.load_wait(timeout)
            return True
        except:
            return False
    
    def location_href(self, url:str):
        '''
        ページ遷移
        '''
        # ポップアップ無効
        self._driver.execute_script('window.onbeforeunload = function() {};')
        self._driver.execute_script(f'window.location.href = "{url}";')
        self.load_wait()
        
    def set_basic_auth_header(self, user_name:str=None, password:str=None, clear_mode:bool=False) -> bool:
        '''
        ベーシック認証の設定
        '''
        try:
            if clear_mode:
                auth_header = {}
            elif all([user_name, password]):
                # Authorizationヘッダを作成
                b64 = base64.b64encode(f'{user_name}:{password}'.encode('utf-8')).decode('utf-8')
                auth_header = {'Authorization': f'Basic {b64}'}
            else:
                raise Exception('設定するユーザ名・パスワードがありません')
            # Authorizationヘッダを適用
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': auth_header})
            return True
        except Exception as e:
            logger.error(f'[ベーシック認証の設定]: 失敗\n{e}')
            return False

    def load_wait(self, timeout:int=20, sleep_time:int=0):
        '''
        コンテンツが読み込まれるまで待機
        '''
        try:
            sleep(sleep_time)
            WebDriverWait(self._driver, timeout).until(
                lambda d: d.execute_script("""
                    return document.readyState === 'complete'
                    && (!window.jQuery || jQuery.active === 0)
                """)
            )
        except Exception as e:
            logger.error(f'ロード待機失敗\n{e}')
    
    def implicitly_wait(self, timeout:int=10):
        '''
        要素が使用可能になるまで待つlogin
        '''
        self._driver.implicitly_wait(timeout)
    
    def set_window_size(self, width:Union[int, str], height:Union[int, str]):
        '''
        画面サイズ変更
        '''
        self._driver.set_window_size(int(width), int(height))

    def exe_js(self, method_str:str, *args, timeout:int=10):
        '''
        javascript実行
        '''
        result = self._driver.execute_script(f'return {method_str}', *args)
        self.load_wait(timeout)
        return result
    
    def remove_read_only(self, ele):
        '''
        リードオンリーのエレメントのリードオンリーを消す
        '''
        self.exe_js("arguments[0].removeAttribute('readonly');", ele)
        return ele
    
    def del_element(self, ele):
        '''
        エレメント削除
        '''
        self.exe_js('arguments[0].remove();', ele)
    
    def set_ele_value(self, ele, val):
        '''
        エレメントのValue変更
        '''
        self.exe_js('arguments[0].value = arguments[1]', ele, val)
    
    def find_element(self, mode:str, word:str, timeout:int=10):
        '''
        エレメント検索
        '''
        elements = self.find_elements(mode, word, timeout, 1) or []
        return elements[0] if len(elements) > 0 else None

    def find_elements(self, mode:str, word:str, timeout:int=10, max_ele_num:int=-1) -> list:
        '''
        エレメント検索(複数)
        '''
        tgt_mode = {
            'id'          : By.ID,
            'class'       : By.CLASS_NAME,
            'tag'         : By.TAG_NAME,
            'name'        : By.NAME,
            'xpath'       : By.XPATH,
            'css_selector': By.CSS_SELECTOR,
            'link_text'   : By.LINK_TEXT,
        }.get(mode)
        try:
            ele_list = WebDriverWait(self._driver, timeout).until(
                EC.presence_of_all_elements_located((tgt_mode, word))
            )
            if max_ele_num != -1:
                ele_list = ele_list[:max_ele_num]
            return [CustomElement(self._driver, ele.id) for ele in ele_list]
        except Exception as e:
            return []
    
    def add_tab(self, switch:bool=True) -> str:
        '''
        タブ追加
        '''
        self._driver.execute_script("window.open('');")
        tab_id = self.tab_id_list[-1]
        if switch:
            self.switch_tab(tab_id)
        return tab_id
    
    def switch_tab(self, tab_id:str):
        '''
        タブ切替
        '''
        self._driver.switch_to.window(tab_id)
    
    def close_tab(self, tab_id:str):
        '''
        タブを閉じる
        '''
        self.switch_tab(tab_id)
        self._driver.close()
        self.switch_tab(self.tab_id_list[0])

    def switch_frame(self, iframe_ele):
        '''
        フレーム変更
        '''
        self._driver.switch_to.frame(iframe_ele)
    
    def switch_parent_frame(self):
        '''
        親フレームに移動
        '''
        self._driver.switch_to.parent_frame()
    
    def switch_default_frame(self):
        '''
        フレームをデフォルトのものに戻す
        '''
        self._driver.switch_to.default_content()

    ####################################################################################################
    # クラスメソッド
    ####################################################################################################
    @classmethod
    def get_select(cls, ele) -> Select:
        '''
        セレクター取得
        '''
        return Select(ele.web_element)