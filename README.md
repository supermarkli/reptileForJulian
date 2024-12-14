# reptileForJulian

一个为巨量算数平台设计的数据采集工具，用于批量获取达人数据。

## 功能特点

- 自动采集达人TGI指数数据
- 自动采集达人粉丝数据
- 支持批量处理多个达人账号
- 自动将数据保存至Excel文件
- 完善的日志记录系统

## 数据来源

[算数指数-巨量算数](https://trendinsight.oceanengine.com/arithmetic-index?type=3)

## 环境要求

- Python 3.8+
- Chrome浏览器
- Chrome WebDriver

## 安装步骤

1. 克隆项目到本地
   git clone [repository_url]
   cd reptileForJulian

2. 安装依赖包
   pip install -r requirements.txt

3. 配置文件设置
   在 config.py 中配置以下内容：
   - Chrome用户数据目录 (CHROME_USER_DATA_DIR)
   - Chrome配置文件 (CHROME_PROFILE)
   - Excel文件路径
   - 批处理参数（大小和间隔时间）

## 使用方法

### 1. 准备数据文件
确保Excel文件（TgiData.xlsx/FansData.xlsx）包含必要的"昵称"列。

### 2. 运行脚本

采集TGI数据：
python TgiRead.py

采集粉丝数据：
python FansRead.py

## 文件说明

- TgiRead.py: TGI指数数据采集脚本
- FansRead.py: 粉丝数据采集脚本
- config.py: 配置文件
- requirements.txt: 项目依赖
- TgiData.xlsx: TGI数据存储文件
- FansData.xlsx: 粉丝数据存储文件

## 数据格式

### TGI数据
- 昵称
- TGI均值
- 其他相关指标

### 粉丝数据
- 昵称
- 日期列（动态生成）
- 粉丝数量

## 注意事项

1. 使用前确保：
   - 已登录巨量算数平台
   - Chrome浏览器配置正确
   - Excel文件格式符合要求

2. 运行建议：
   - 合理设置批处理间隔，避免请求过于频繁
   - 定期检查日志输出
   - 保持网络稳定

3. 数据安全：
   - 定期备份数据文件
   - 请勿修改正在处理的Excel文件

## 错误处理

如遇到问题，请检查：
1. 网络连接状态
2. Chrome浏览器版本
3. 登录状态
4. Excel文件是否被占用

## 更新日志

### v1.0.0
- 实现基础数据采集功能
- 支持TGI和粉丝数据批量获取
- 添加日志记录系统
