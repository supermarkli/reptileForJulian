# config.py

class Config:
    # URL配置
    BASE_URL = "https://trendinsight.oceanengine.com/arithmetic-index?type=3"
    SEARCH_BASE_URL = "https://trendinsight.oceanengine.com/arithmetic-index/daren/search?keyword="
    API_URL = "https://trendinsight.oceanengine.com/api/v2/daren/get_great_user_fans_info"

    # 文件配置
    TGI_EXCEL_FILE = "TgiData.xlsx"
    FANS_EXCEL_FILE = "FansData.xlsx"
    SHEET_NAME = "Sheet1"
    NICKNAME_COLUMN = "昵称"
    TGI_COLUMN = "TGI均值"

    # Chrome配置
    CHROME_USER_DATA_DIR = r"C:\Users\undefined\AppData\Local\Google\Chrome\User Data"
    CHROME_PROFILE = "Default"

    # 等待时间配置
    WAIT_TIMEOUT = 20  # 显式等待超时时间
    BATCH_SIZE = 10    # 每批处理的数量
    BATCH_INTERVAL = 1 # 批次间隔时间(秒)

    # CSS选择器配置
    SELECTORS = {
        'loading': '.loading-spinner',
        'search_result': '.item-p2pF9O',
        'daren_detail': '.daren-CJ5hTJ',
        'fans_profile': 'div.item-a_379S:nth-child(3)',
        'data_container': '.fans-portrait-container'
    }

    # 日志配置
    LOG_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(levelname)s - %(message)s'
    }