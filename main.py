import os
import pandas as pd
from urllib.parse import quote
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class TGIDataProcessor:
    def __init__(self):
        self.base_url = "https://trendinsight.oceanengine.com/arithmetic-index?type=3"
        self.excel_file = "data.xlsx"
        self.search_base_url = "https://trendinsight.oceanengine.com/arithmetic-index/daren/search?keyword="

        # 设置 Chrome 选项
        logging.info("初始化Chrome WebDriver")
        chrome_options = Options()
        # 使用默认的 Chrome 用户配置文件
        chrome_options.add_argument(
            r"user-data-dir=C:\Users\undefined\AppData\Local\Google\Chrome\User Data")
        # 指定配置文件
        chrome_options.add_argument("profile-directory=Default")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        logging.info("Chrome WebDriver初始化完成")

    def read_tgi_data(self):
        """读取Excel文件中的TGI指数数据"""
        try:
            if not os.path.exists(self.excel_file):
                logging.error(f"错误：找不到文件 {self.excel_file}")
                return None

            # 指定读取"TGI指数平均值"工作表
            df = pd.read_excel(self.excel_file, sheet_name="TGI指数平均值")
            logging.info(f"成功读取'TGI指数平均值'工作表")

            # 显示工作表的基本信息
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
            logging.info(f"访问搜索URL: {search_url}")
            self.driver.get(search_url)

            # 等待加载完成
            self._wait_for_loading()

            # 获取搜索结果
            results = self._get_search_results()
            if not results:
                logging.warning(f"昵称 {nickname} 没有搜索结果")
                return

            # 处理第一个搜索结果
            first_result = results[0]
            self._process_first_result(first_result, nickname)

        except Exception as e:
            self._handle_search_error(e, nickname, original_handles)

    def _wait_for_loading(self):
        """等待页面加载完成"""
        try:
            loading_selector = ".loading-spinner"
            WebDriverWait(self.driver, 5).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, loading_selector))
            )
            logging.info("页面加载完成")
        except Exception as e:
            logging.debug(f"未检测到加载指示器: {str(e)}")

    def _get_search_results(self):
        """获取搜索结果"""
        try:
            results = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".item-p2pF9O"))
            )
            logging.info(f"找到 {len(results)} 个搜索结果")
            return results
        except Exception as e:
            logging.error(f"获取搜索结果时出错: {str(e)}")
            return []

    def _process_first_result(self, first_result, nickname):
        """处理第一个搜索结果"""
        try:
            # 在搜索结果中找到"达人详情"按钮
            daren_detail_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".daren-CJ5hTJ"))
            )

            # 滚动到按钮位置并点击
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", 
                daren_detail_button
            )
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", daren_detail_button)
            logging.info(f"成功点击 {nickname} 的达人详情按钮")
            
            # 等待页面跳转和canvas加载
            time.sleep(0.5)
            
            # 获取TGI数据
            tgi_values = self.driver.execute_script("""
                // 获取所有tooltip中的TGI值
                var tooltips = document.querySelectorAll('.lightcharts-tooltip');
                var values = [];
                
                tooltips.forEach(function(tooltip) {
                    var tgiRow = Array.from(tooltip.querySelectorAll('div')).find(div => 
                        div.textContent.includes('TGI')
                    );
                    if (tgiRow) {
                        var tgiValue = parseFloat(tgiRow.querySelector('span:last-child').textContent);
                        if (!isNaN(tgiValue)) {
                            values.push(tgiValue);
                        }
                    }
                });
                
                return values;
            """)
            
            # 计算平均值
            if tgi_values and len(tgi_values) > 0:
                avg_tgi = sum(tgi_values) / len(tgi_values)
                logging.info(f"昵称 {nickname} 的TGI值: {tgi_values}")
                logging.info(f"昵称 {nickname} 的TGI平均值: {avg_tgi}")
            else:
                logging.warning(f"未能获取到 {nickname} 的TGI值")
            
            # 记录URL
            logging.info(f"跳转后的页面URL: {self.driver.current_url}")

        except Exception as e:
            logging.error(f"处理达人详情时出错: {str(e)}")
            raise

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

        nickname_column = "昵称"

        if nickname_column not in df.columns:
            logging.error(f"错误：找不到'{nickname_column}'列")
            logging.error(f"可用的列名：{list(df.columns)}")
            return

        # 获取所有不重复的昵称
        nicknames = df[nickname_column].unique()
        logging.info(f"共找到 {len(nicknames)} 个不重复昵称")

        # 搜索每个昵称
        for i, nickname in enumerate(nicknames, 1):
            logging.info(f"\n处理第 {i}/{len(nicknames)} 个昵称")
            self.search_nickname(nickname)

            # 每处理3个昵称暂停一下，避免打开太多标签页
            if i % 3 == 0:
                input("已打开3个搜索页面，按回车继续...")

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
