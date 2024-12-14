# FansRead.py
import os
import pandas as pd
from urllib.parse import quote
import time
import logging
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from config import Config
# 配置日志
logging.basicConfig(
    level=Config.LOG_CONFIG['level'],
    format=Config.LOG_CONFIG['format']
)


class FansDataProcessor:
    def __init__(self):
        self.base_url = Config.BASE_URL
        self.excel_file = Config.FANS_EXCEL_FILE
        self.search_base_url = Config.SEARCH_BASE_URL

        # 初始化浏览器驱动
        try:
            logging.info("初始化Chrome WebDriver")
            chrome_options = Options()
            chrome_options.set_capability(
                'goog:loggingPrefs', {'performance': 'ALL'})
            chrome_options.add_argument(
                f"user-data-dir={Config.CHROME_USER_DATA_DIR}")
            chrome_options.add_argument(
                f"profile-directory={Config.CHROME_PROFILE}")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, Config.WAIT_TIMEOUT)
            logging.info("Chrome WebDriver初始化完成")
        except Exception as e:
            logging.error(f"初始化浏览器驱动失败: {str(e)}")
            raise

    def read_fans_data(self):
        """读取Excel文件中的数据"""
        try:
            if not os.path.exists(self.excel_file):
                logging.error(f"错误：找不到文件 {self.excel_file}")
                return None

            df = pd.read_excel(self.excel_file, sheet_name=Config.SHEET_NAME)
            logging.info(f"成功读取'{Config.SHEET_NAME}'工作表")
            logging.info(f"工作表包含 {len(df)} 行数据")
            logging.info(f"列名：{list(df.columns)}")
            return df

        except Exception as e:
            logging.error(f"读取文件 {self.excel_file} 时发生错误: {str(e)}")
            return None

    def search_nickname(self, nickname):
        """根据昵称搜索"""
        try:
            # 记录当前标签页
            original_handles = self.driver.window_handles
            logging.info(f"开始处理昵称: {nickname}")

            # 访问搜索URL
            encoded_nickname = quote(nickname)
            search_url = self.search_base_url + encoded_nickname
            self.driver.get(search_url)

            # 等待加载完成
            self._wait_for_loading()

            # 获取搜索结果
            results = self._get_search_results()
            if not results:
                logging.warning(f"昵称 {nickname} 没有搜索结果")
                return

            self._process_first_result(nickname)

        except Exception as e:
            self._handle_search_error(e, nickname, original_handles)

    def _wait_for_loading(self):
        """等待页面加载完成"""
        try:
            self.wait.until_not(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, Config.SELECTORS['loading']))
            )
            logging.info("页面加载完成")
        except Exception as e:
            logging.debug(f"未检测到加载指示器: {str(e)}")

    def _get_search_results(self):
        """获取搜索结果"""
        try:
            results = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, Config.SELECTORS['search_result']))
            )
            return results
        except Exception as e:
            logging.error(f"获取搜索结果时出错: {str(e)}")
            return []

    def _process_first_result(self, nickname):
        """
        处理搜索结果中的第一个达人详情
        Args:
            nickname: 达人昵称
        """
        try:
            # 点击达人详情按钮
            self._click_daren_detail(nickname)
            
            # 获取并处理粉丝数据
            self._process_fans_data(nickname)
            
        except Exception as e:
            logging.error(f"处理达人详情时发生错误: {str(e)}")
            raise
        finally:
            self._clean_up_windows()

    def _process_fans_data(self, nickname):
        """处理粉丝数据"""
        logs = self.driver.get_log('performance')
        target_url = "https://trendinsight.oceanengine.com/api/v2/daren/get_great_user_mile_Info"
        
        for entry in logs:
            try:
                if not self._is_target_request(entry, target_url):
                    continue
                    
                fans_data = self._extract_fans_data(entry)
                if not fans_data:
                    continue
                    
                self._log_fans_details(nickname, fans_data)
                self._update_excel_file(nickname, fans_data)
                break
                
            except Exception as e:
                logging.error(f"处理网络日志时出错: {str(e)}")
                continue

    def _extract_fans_data(self, entry):
        """提取粉丝数据"""
        message = json.loads(entry['message'])
        request_id = message['message']['params']['requestId']
        response = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
        response_data = json.loads(response['body'])
        return response_data['data']['fanslistday']

    def _log_fans_details(self, nickname, fans_data):
        """记录粉丝数据详情"""
        logging.info(f"\n昵称 {nickname} 的粉丝数据详情:")
        for item in fans_data:
            logging.info(f"日期: {item['date']}, 数量: {item['count']}")

    def _update_excel_file(self, nickname, fans_data):
        """更新Excel文件中的粉丝数据"""
        try:
            df = pd.read_excel(self.excel_file)
            mask = df['昵称'] == nickname
            
            if mask.any():
                # 将fans_data按日期排序
                sorted_fans_data = sorted(fans_data, key=lambda x: x['date'])
                
                # 为每个日期创建新列（如果不存在）
                for item in sorted_fans_data:
                    date = item['date']
                    count = int(item['count'])  # 确保count是整数类型
                    
                    if date not in df.columns:
                        # 创建新列时指定数据类型为Int64（可以处理空值的整数类型）
                        df[date] = pd.Series(dtype='Int64')
                    
                    # 使用astype确保类型一致
                    df.loc[mask, date] = count
                
                # 重新排序列：保持'排名'和'昵称'列在最前，其他列按日期排序
                fixed_columns = ['排名', '昵称']
                date_columns = [col for col in df.columns if col not in fixed_columns]
                date_columns.sort()
                new_columns = fixed_columns + date_columns
                df = df[new_columns]
                
                df.to_excel(self.excel_file, index=False)
                logging.info(f"已将 {nickname} 的粉丝数据按日期顺序保存到Excel文件")
            else:
                logging.warning(f"在Excel文件中未找到昵称 {nickname}")
                
        except Exception as e:
            logging.error(f"更新Excel文件时出错: {str(e)}")

    def _click_daren_detail(self, nickname):
        """点击达人详情按钮"""
        logging.info(f"开始处理昵称: {nickname} 的达人详情")
        daren_detail_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".daren-CJ5hTJ"))
        )
        
        self._scroll_and_click(daren_detail_button)
        logging.info(f"已点击 {nickname} 的达人详情按钮")
        self._wait_for_loading()
        time.sleep(1)

   
    def _scroll_and_click(self, element):
        """滚动到元素位置并点击"""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        self.driver.execute_script("arguments[0].click();", element)

    def _is_target_request(self, entry, target_url):
        """检查是否为目标请求"""
        message = json.loads(entry['message'])
        if 'message' not in message or message['message']['method'] != 'Network.responseReceived':
            return False
        return target_url in message['message']['params']['response']['url']


    def _clean_up_windows(self):
        """清理浏览器窗口"""
        if len(self.driver.window_handles) > 1:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

    def _handle_search_error(self, error, nickname, original_handles):
        """处理搜索过程中的错误"""
        logging.error(f"搜索昵称 {nickname} 时发生错误: {str(error)}")
        logging.error(f"错误类型: {type(error).__name__}")

        # 恢复到原始状态
        if len(self.driver.window_handles) > len(original_handles):
            logging.info("检测到多余标签页，正在关闭...")
            self.driver.close()
            self.driver.switch_to.window(original_handles[0])
            logging.info("已恢复到原始标签页")

    def process_nicknames(self, df):
        """处理所有昵称"""
        if df is None or df.empty:
            logging.error("没有数据可处理")
            return

        if Config.NICKNAME_COLUMN not in df.columns:
            logging.error(f"错误：找不到'{Config.NICKNAME_COLUMN}'列")
            logging.error(f"可用的列名：{list(df.columns)}")
            return

        nicknames = df[Config.NICKNAME_COLUMN].unique()
        logging.info(f"共找到 {len(nicknames)} 个不重复昵称")

        for i in range(0, len(nicknames), Config.BATCH_SIZE):
            batch = nicknames[i:i + Config.BATCH_SIZE]
            logging.info(f"\n开始处理第 {i+1}-{min(i+Config.BATCH_SIZE, len(nicknames))}/{len(nicknames)} 批昵称")
            
            for nickname in batch:
                self.search_nickname(nickname)
            
            if i + Config.BATCH_SIZE < len(nicknames):
                logging.info(f"批次处理完成，暂停{Config.BATCH_INTERVAL}秒...")
                time.sleep(Config.BATCH_INTERVAL)

    def __del__(self):
        """析构函数，确保关闭浏览器"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logging.info("浏览器已关闭")

    def run(self):
        """运行主程序"""
        df = self.read_fans_data()
        self.process_nicknames(df)


if __name__ == "__main__":
    processor = FansDataProcessor()
    processor.run()
