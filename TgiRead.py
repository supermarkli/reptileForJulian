# TgiRead.py
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


class TGIDataProcessor:
    def __init__(self):
        self.base_url = Config.BASE_URL
        self.excel_file = Config.EXCEL_FILE
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

    def read_tgi_data(self):
        """读取Excel文件中的TGI指数数据"""
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
        """处理第一个搜索结果"""
        try:
            # 在搜索结果中找到"达人详情"按钮
            logging.info(f"开始处理昵称: {nickname} 的达人详情")
            daren_detail_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".daren-CJ5hTJ"))
            )

            # 记录当前窗口句柄
            original_handle = self.driver.current_window_handle

            # 滚动到按钮位置并点击
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                daren_detail_button
            )

            # 使用 JavaScript 点击按钮
            self.driver.execute_script(
                "arguments[0].click();", daren_detail_button)
            logging.info(f"已点击 {nickname} 的达人详情按钮")

            self._wait_for_loading()

            original_handle = self.driver.current_window_handle

            fans_profile_selector = "div.item-a_379S:nth-child(3)"

            # 等待并点击粉丝画像按钮
            fans_profile_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, fans_profile_selector))
            )

            # 滚动到粉丝画像按钮位置
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                fans_profile_button
            )

            # 点击粉丝画像按钮
            self.driver.execute_script(
                "arguments[0].click();", fans_profile_button)
            logging.info(f"已点击 {nickname} 的粉丝画像按钮")

            time.sleep(1)

            # 使用 CDP (Chrome DevTools Protocol) 获取网络请求
            logs = self.driver.get_log('performance')

            # 查找目标API请求
            target_url = "https://trendinsight.oceanengine.com/api/v2/daren/get_great_user_fans_info"
            for entry in logs:
                try:
                    message = json.loads(entry['message'])
                    if 'message' in message and message['message']['method'] == 'Network.responseReceived':
                        request_url = message['message']['params']['response']['url']
                        if target_url in request_url:
                            # 获取请求ID和响应内容
                            request_id = message['message']['params']['requestId']
                            response = self.driver.execute_cdp_cmd(
                                'Network.getResponseBody', {'requestId': request_id})

                            # 解析响应数据
                            response_data = json.loads(response['body'])
                            city_label_tgi = json.loads(
                                response_data['data']['CityLabel_Tgi'])

                            # 显示每个城市等级的TGI值
                            logging.info(f"\n昵称 {nickname} 的城市等级TGI详情:")
                            for item in city_label_tgi:
                                logging.info(f"{item['name']}: {
                                             item['value']:.2f}")

                            # 计算TGI平均值
                            tgi_values = [item['value']
                                          for item in city_label_tgi]
                            average_tgi = sum(tgi_values) / len(tgi_values)

                            # 更新Excel文件
                            try:
                                df = pd.read_excel(self.excel_file)
                                # 找到对应昵称的行
                                mask = df['昵称'] == nickname
                                if mask.any():
                                    # 如果"TGI均值"列不存在，创建该列
                                    if 'TGI均值' not in df.columns:
                                        df['TGI均值'] = None
                                    # 更新TGI均值
                                    df.loc[mask, 'TGI均值'] = average_tgi
                                    # 保存更新后的Excel文件
                                    df.to_excel(self.excel_file, index=False)
                                    logging.info(f"已将 {nickname} 的TGI均值 {
                                                 average_tgi:.2f} 保存到Excel文件")
                                else:
                                    logging.warning(
                                        f"在Excel文件中未找到昵称 {nickname}")
                            except Exception as e:
                                logging.error(f"更新Excel文件时出错: {str(e)}")

                            logging.info(f"\n总计算过程:")
                            logging.info(f"总和: {sum(tgi_values):.2f}")
                            logging.info(f"城市等级数量: {len(tgi_values)}")
                            logging.info(f"平均值: {average_tgi:.2f}")
                            break
                except Exception as e:
                    logging.error(f"处理网络日志时出错: {str(e)}")
                    continue

        except Exception as e:
            logging.error(f"处理达人详情时发生错误: {str(e)}")
            raise
        finally:
            # 确保关闭当前标签页并切回原标签页
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(original_handle)

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
        df = self.read_tgi_data()
        self.process_nicknames(df)


if __name__ == "__main__":
    processor = TGIDataProcessor()
    processor.run()
