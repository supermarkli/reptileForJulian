import os
import pandas as pd
from urllib.parse import quote
import webbrowser
import time

class TGIDataProcessor:
    def __init__(self):
        self.base_url = "https://trendinsight.oceanengine.com/arithmetic-index?type=3"
        self.excel_file = "data.xlsx"
        self.search_base_url = "https://trendinsight.oceanengine.com/arithmetic-index/daren/search?keyword="
        
    def read_tgi_data(self):
        """读取Excel文件中的TGI指数数据"""
        try:
            if not os.path.exists(self.excel_file):
                print(f"错误：找不到文件 {self.excel_file}")
                return None
                
            # 指定读取"TGI指数平均值"工作表
            df = pd.read_excel(self.excel_file, sheet_name="TGI指数平均值")
            print(f"成功读取'TGI指数平均值'工作表")
            
            # 显示工作表的基本信息
            print(f"工作表包含 {len(df)} 行数据")
            print(f"列名：{list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"读取文件 {self.excel_file} 时发生错误: {str(e)}")
            return None

    def search_nickname(self, nickname):
        """根据昵称搜索"""
        try:
            encoded_nickname = quote(nickname)
            search_url = self.search_base_url + encoded_nickname
            
            # 使用webbrowser打开搜索页面
            webbrowser.open(search_url)
            print(f"已打开昵称 {nickname} 的搜索页面")
            
            # 短暂等待以避免打开太多页面
            time.sleep(1)
            
        except Exception as e:
            print(f"处理昵称 {nickname} 时发生错误: {str(e)}")

    def process_nicknames(self, df):
        """处理所有昵称"""
        if df is None or df.empty:
            print("没有数据可处理")
            return
            
        nickname_column = "昵称"
        
        if nickname_column not in df.columns:
            print(f"错误：找不到'{nickname_column}'列")
            print(f"可用的列名：{list(df.columns)}")
            return
            
        # 获取所有不重复的昵称
        nicknames = df[nickname_column].unique()
        print(f"共找到 {len(nicknames)} 个不重复昵称")
        
        # 搜索每个昵称
        for i, nickname in enumerate(nicknames, 1):
            print(f"\n处理第 {i}/{len(nicknames)} 个昵称")
            self.search_nickname(nickname)
            
            # 每处理3个昵称暂停一下，避免打开太多标签页
            if i % 3 == 0:
                input("已打开3个搜索页面，按回车继续...")

    def run(self):
        """运行主程序"""
        df = self.read_tgi_data()
        self.process_nicknames(df)

if __name__ == "__main__":
    processor = TGIDataProcessor()
    processor.run() 