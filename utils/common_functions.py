import logging
from typing import Union

logger = logging.getLogger(__name__)

# メソッド ============================================================================================
def birthday_to_age(year:Union[str, int], month:Union[str, int], day:Union[str, int]) -> int:
    '''
    生年月日から年齢を算出する
    Args:
        year  (Union[str, int]): 誕生年
        month (Union[str, int]): 誕生月
        day   (Union[str, int]): 誕生日
    Returns:
        int: 年齢
    '''
    now_date = now(alert=False)
    age = now_date.year - int(year) - ((now_date.month, now_date.day) < (int(month), int(day)))
    return age

def clear_dir_recursive(dir_path:str):
    '''
    ディレクトリ配下を空にする
    '''
    import os
    import shutil
    for entry in os.scandir(dir_path):
        try:
            if entry.is_symlink():
                # シンボリックリンクはリンク先を辿らずリンク自体だけ消す
                os.unlink(entry.path)
            elif entry.is_dir(follow_symlinks=False):
                # ディレクトリの場合
                shutil.rmtree(entry.path)
            else:
                # ファイルの場合
                os.remove(entry.path)
        except FileNotFoundError:
            # 途中で別プロセスが消した場合は無視
            pass

def cpu_count() -> int:
    '''
    CPUのコア数取得
    Returns:
        int: CPUコア数
    '''
    import os
    return os.cpu_count()

def datetime_2_str(date_obj:object, format:str) -> str:
    '''
    日付型を指定のフォーマットの文字列にする
    Args:
        date_obj  (object): 日付型のオブジェクト
        format    (str)   : 変換するフォーマット
    Returns:
        str: 文字列に変換した日付
    '''
    import datetime
    return date_obj.strftime(format)

def dict_list_to_dict(doct_list:list[dict]) -> dict:
    '''
    辞書のリストをまとめる
    Args:
        doct_list (list[dict]): 辞書のリスト
        ※例
        profile_dict_list = [
            {'name': 'Taro',    'age': 45},
            {'name': 'Hanako',  'age': 50},
            {'name': 'Francis', 'age': 16},
        ]
    Returns:
        dict: キーごとにリストにして返却
        ※例
        {'name': ['Taro', 'Hanako', 'Francis'], 'age': [45, 50, 16]}
    '''
    result_dict = {key: [tgt_dict[key] for tgt_dict in doct_list] for key in doct_list[0].keys()}
    return result_dict

def find_list_index(tgt_list:list, search_item:object, list_mode:bool=False) -> Union[list, int]:
    '''
    リストの中に一致するワードがあればそのインデックスのリストを返却する
    Args:
        tgt_list    (list)  : 探査対象のリスト
        search_item (object): 探査ワード
        list_mode   (bool)  : リストで返却するか否か
    Returns:
        Union[list, int]: 一致したインデックスのリスト、または初めに一致したインデックス
    '''
    if list_mode:
        result = [i for i, tgt in enumerate(tgt_list) if tgt==search_item]
    else:
        result = -1
        for i, tgt in enumerate(tgt_list):
            if tgt==search_item:
                result = i
                break
    return result

def han_to_zen(text:str) -> str:
    '''
    半角英数字を全角に変換
    Args:
        text (str): 変換対象文字列
    Returns:
        text: 全角文字列
    '''
    result_text = ''.join(chr(ord(char) + 0xFEE0) if '!' <= char <= '~' else char for char in text)
    result_text = result_text.replace(' ', '　')
    return result_text

def lazy_import(module_name:str):
    '''
    遅延インポート
    '''
    import importlib
    return importlib.import_module(module_name)

def month_date_list(year:Union[int, str], month:Union[int, str]) -> list:
    '''
    入力された月の一覧を取得する
    Args:
        year　(Union[int, str]): 対象の年
        month (Union[int, str]): 対象の月
    Returns:
        list: 対象月のdateオブジェクトのリスト
    '''
    import datetime
    # 引数をINTに変換
    year, month = map(int, [year, month])
    # 月開始日
    start_date = datetime.date(year, month, 1)
    # 月終了日
    end_date = datetime.date(year, month+1, 1) - datetime.timedelta(days=1) \
        if month!= 12 else datetime.date(year+1, 1, 1) - datetime.timedelta(days=1)
    date_list = [start_date]
    for i in range(1, (end_date - start_date).days):
        date_list.append(start_date + datetime.timedelta(days=i))
    date_list.append(end_date)
    return date_list

def now(time_zone:str='Asia/Tokyo', alert:bool=True) -> object:
    '''
    入力された月の一覧を取得する
    Args:
        time_zone (str) : タイムゾーン
        alert     (bool): タイムゾーン取得失敗時にエラーメッセージを出すかどうか
    Returns:
        object: 現在日時のdatatimeオブジェクト
    '''
    import datetime, zoneinfo
    try:
        return datetime.datetime.now(zoneinfo.ZoneInfo(time_zone))
    except zoneinfo.ZoneInfoNotFoundError:
        if alert:
            logger.warning(f'警告: {time_zone}キーでタイムゾーンが検出できません。ローカル時間を使用しています。')
        return datetime.datetime.now()

def retry_function(func, *args, max_attempts:int=3, delay:float=1, exceptions:tuple=(Exception,), **kwargs):
    '''
    指定関数を実行し、例外発生時にリトライ処理を行う汎用ラッパ関数
    Args:
        func              : 実行対象の関数
        *args             : func に渡す位置引数
        max_attempts (int): 最大リトライ回数（デフォルト: 3）
        delay (float)     : リトライ間隔（秒）（デフォルト: 1）
        exceptions (tuple): リトライ対象とする例外クラスのタプル（デフォルト: (Exception,)）
        **kwargs          : func に渡すキーワード引数（デフォルト引数の上書き含む）
    Returns:
        T: func の戻り値
    Raises:
        Exception: max_attempts 回すべて失敗した場合、最後に発生した例外を再送出する
    '''
    last_exception = None
    for attempt in range(1, max_attempts+1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            logger.warning(f'{func.__name__} 例外発生: {e}\n{delay}秒後に{attempt}回目の再試行を実行します')
            time.sleep(delay)
    logger.error(f'{max_attempts}回再試行しましたがすべて失敗しました: {func.__name__}')
    raise last_exception

def str_2_datetime(date_str:str, format:str):
    '''
    文字列を指定フォーマットで datetime に変換する
    Args:
        date_str (str): 日付文字列
        format   (str): 日付フォーマット
    Returns:
        datetime.datetime: datetime オブジェクト
    '''
    import datetime
    return datetime.datetime.strptime(date_str, format)

def zen_to_han(text:str) -> str:
    '''
    全角英数字を半角に変換
    Args:
        text (str) : 変換対象文字列
    Returns:
        text: 半角文字列
    '''
    result_text = ''.join(chr(ord(char) - 0xFEE0) if '！' <= char <= '～' else char for char in text)
    result_text = result_text.replace('　', ' ')
    return result_text
# ====================================================================================================

# デコレータ用 ========================================================================================
def check_process_time(func):
    '''
    関数の実行時間測定用
    '''
    import functools
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        logger.info('処理開始')
        start  = now(alert=False)
        result = func(*args, **kwargs)
        end    = now(alert=False)
        logger.info(f'処理終了:{(p_time:=(end - start)).total_seconds():.6f}秒')
        return result
    return _wrapper

def multi_thread_execution(max_workers:int):
    '''
    関数をマルチスレッドで実行するデコレータのファクトリ
    '''
    def _decorator(func):
        import concurrent.futures
        import functools
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                if args and kwargs:
                    futures = [
                        executor.submit(func, *arg, **{key: val for key, val in zip(kwargs.keys(), kv_set)})
                        for arg, kv_set in zip(zip(*args), zip(*kwargs.values()))
                    ]
                    result_list = [f.result() for f in futures]
                elif kwargs:
                    futures = [
                        executor.submit(func, **{key: val for key, val in zip(kwargs.keys(), kv_set)})
                        for kv_set in zip(*kwargs.values())
                    ]
                    result_list = [f.result() for f in futures]
                else:
                    result_list = list(executor.map(func, *args))
            return result_list
        return _wrapper
    return _decorator
# ====================================================================================================

# テスト実行用
if __name__ == '__main__':
    # multi_thread_execution使い方サンプル ================================================================
    @multi_thread_execution(max_workers=4)
    def show_profile(no:int, name:str, age:int):
        '''
        プロフィールを表示する（テスト関数）
        '''
        result = f'No:{no} {name=} {age=}'
        logger.info(result)
        return result
    # プロフィール
    profile_dict_list = [
        {'name': 'Taro',    'age': 45},
        {'name': 'Hanako',  'age': 50},
        {'name': 'Francis', 'age': 16},
        {'name': 'Kameko',  'age': 106},
    ]
    result_list = show_profile(range(1, 5), **dict_list_to_dict(profile_dict_list))
    # ====================================================================================================
    import pdb;pdb.set_trace()