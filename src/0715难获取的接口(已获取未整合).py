import os
import json
import numpy as np
import pandas as pd
import akshare as ak
import inspect
from datetime import date, datetime, timedelta
from basic_func import DateEncoder
from basic_func import save_to_json
from basic_func import save_to_json_v2
from basic_func import load_json
from basic_func import load_json_df
from basic_func import get_yesterday
from basic_func import processing_date
from basic_func import find_latest_file
from basic_func import find_latest_file_v2
from basic_func import stock_traversal_module
from basic_func import get_matching_h_stocks
from basic_func import create_dict

holidays = [
    "20240101",  # 元旦
    "20240210", "20240211", "20240212", "20240213", "20240214", "20240215", "20240216",  # 春节
    "20240405",  # 清明节
    "20240501",  # 劳动节
    "20240609", "20240610", "20240611",  # 端午节
    "20240913", "20240914", "20240915",  # 中秋节
    "20241001", "20241002", "20241003", "20241004", "20241005", "20241006", "20241007",  # 国庆节
]


def generate_quarters(begin_date, end_date):
    start = datetime.strptime(begin_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    quarters = []

    while start <= end:
        year = start.year
        month = start.month
        quarter = (month - 1) // 3 + 1
        quarter_str = f"{year}{quarter}"
        if quarter_str not in quarters:
            quarters.append(quarter_str)
        if quarter == 4:
            start = datetime(year + 1, 1, 1)
        else:
            start = datetime(year, (quarter * 3) + 1, 1)
    return quarters
# print(ak.stock_sector_spot("新浪行业"))
# print(ak.stock_sector_spot("启明星行业"))
# print(ak.stock_sector_spot("概念"))
# print(ak.stock_sector_spot("地域"))
# print(ak.stock_sector_spot("行业"))

# print(ak. stock_lhb_stock_detail_date_em(symbol="600077"))

# print(ak. stock_analyst_rank_em())

# print(ak.stock_fund_stock_holder("600077"))

# print(ak.stock_sy_hy_em(date="20240331"))  # 季报

# 将上面的输出的label转换为词典，写一个遍历词典的函数

# def stock_sector_detail():
#     # 取label列
#     df = ak.stock_sector_spot("新浪行业")
#     ak.stock_sector_spot("概念")
#     ak.stock_sector_spot("地域")
#     ak.stock_sector_spot("行业")
#
#
#
#     ak.stock_sector_detail(sector=f"{}")

def relative_traversal_module(func, basic_name, dict, args, base_path='./stock_data/stock_relative',
                           report_date=get_yesterday(), get_full_file=False, individual_file=True):
    """
    获取每日报表
    :param func: 调用的接口函数
    :param dict: 通用，输入的字典
    :param args: 接口需要的股票代码外的参数
    :param base_path: 每日报表生成的基本路径
    :param report_date: 数据储存时文件的后缀id，默认为日期，为日期时可用find_latest_date函数
    :param get_full_file: bool类型，如果要将所有遍历获取的数据额外存储在一个文件中，设为True，默认为False
    :param individual_file: bool类型，数据文件存储公司文件夹还是深沪A股的大文件夹，默认为True即存入公司文件夹
    :return: 无返回值，直接写入文件并存储
    """

    # report_date = "20240710" # 操作标识号，默认为昨天的日期
    # 加载中断点记录
    interrupt_file = os.path.join(base_path, f'{basic_name}_interrupt_{report_date}.json')
    interrupt_data = load_json(interrupt_file)
    if dict.size == 0:
        interrupt_data = {}
    processed_stocks = set(interrupt_data.get('processed_stocks', []))
    # 错误报告的读取
    error_file = os.path.join(base_path, f"{basic_name}_error_reports_{report_date}.json")
    error_reports = load_json(error_file)
    error_reports = []
    if not isinstance(error_reports, list):
        error_reports = []
    # 已处理数据的读取，用于获取完整内容
    if get_full_file:
        data_file = os.path.join(base_path, f"{basic_name}_full_data_{report_date}.json")
        processed_data = load_json(data_file)
        if not isinstance(processed_data, list):
            processed_data = []

    temp_args = inspect.signature(func).parameters
    if "symbol" in temp_args:
        is_symbol = True
    elif "sector" in temp_args:
        is_symbol = False
        is_sector = True
    elif "analyst_id" in temp_args:
        is_symbol = False
        is_sector = False

    dirpath = os.path.join(base_path, f"{basic_name}")
    os.makedirs(dirpath, exist_ok=True)

    # 遍历所有股票的字段
    total_stocks = len(dict)
    for i, unique_code in enumerate(dict):
        # 需要修改，为对应主键

        # 跳过已处理的股票
        if unique_code in processed_stocks:
            # print(f"公司 {stock_name} 代码 {unique_code}已处理，跳过 ")
            continue
        try:
            # # 先计算存储路径；将内容装在入对应公司文件夹中
            # company_name = stock["名称"].strip()  # 去除名称两端的空格
            # # 如果公司名称以 "ST" 开头，则跳过当前循环
            # if company_name.startswith("ST") or company_name.startswith("*ST"):
            #     continue
            # # 替换非法字符
            # company_name_safe = company_name.replace("*", "")  # 替换 * 字符
            # market = "深A股" if flag else "沪A股"
            # # # 写入的文件路径
            # if individual_file:
            #     targeted_filepath = os.path.join(base_path, market, company_name_safe)
            # else:
            #     targeted_filepath = os.path.join(base_path, market)  # 个股信息存储的路径
            # os.makedirs(os.path.join(targeted_filepath, company_name_safe), exist_ok=True)
            # filepath = os.path.join(targeted_filepath, f"{company_name_safe}_{basic_name}_{report_date}.json")
            #
            # # 通过args传递接口的其它参数
            if is_symbol:
                interface_df = func(symbol=unique_code, **args)
            elif is_sector:
                interface_df = func(sector=unique_code, **args)
            else:
                interface_df = func(analyst_id=unique_code, **args)

            if not isinstance(interface_df, pd.DataFrame):
                raise ValueError(f"{basic_name}: {unique_code} does not return DataFrame ")
            if interface_df.empty:
                print(f"Fail to fetch {unique_code} data，interface：{basic_name}")
                error_reports.append({"unique_code": unique_code,
                                      "Error": f"From {basic_name} return empty dataframe"})
                continue
            # 确保日期字段转换为字符串格式
            for col in interface_df.columns:
                if pd.api.types.is_datetime64_any_dtype(interface_df[col]):
                    interface_df[col] = interface_df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
                elif pd.api.types.is_object_dtype(interface_df[col]):
                    interface_df[col] = interface_df[col].astype(str)

            # 记录已处理的股票
            processed_stocks.add(unique_code)
            filepath = os.path.join(dirpath, f"{unique_code}_{report_date}.json")
            save_to_json_v2(interface_df, filepath)

            # 定期保存中间结果和中断点
            if (i + 1) % 10 == 0 or i == total_stocks - 1:
                if get_full_file:
                    save_to_json(processed_data, data_file)
                save_to_json({"processed_stocks": list(processed_stocks)}, interrupt_file)
                save_to_json(error_reports, error_file)
                print(f"Now in {basic_name}")
                print(f"Progress: {i + 1}/{total_stocks} stocks processed.")

        except Exception as e:
            print(f"Error processing stock {unique_code}: {e}")
            error_reports.append({"unique_code": unique_code,  "Error": str(e)})
            if (i + 1) % 10 == 0 or i == total_stocks - 1:
                if get_full_file:
                    save_to_json(processed_data, data_file)
                save_to_json({"processed_stocks": list(processed_stocks)}, interrupt_file)
                save_to_json(error_reports, error_file)
                print(f"Now in {basic_name}")
                print(f"Progress: {i + 1}/{total_stocks} stocks processed.")
            continue

        # 保存最终结果
        if get_full_file:
            save_to_json(processed_data, data_file)
        save_to_json({"processed_stocks": list(processed_stocks)}, interrupt_file)
        save_to_json(error_reports, error_file)

def stock_sector_detail(report_date, base_path='./stock_data/stock_relative'):
    # 后续可以考虑加文件提取
    existing = True
    if existing:
        sina_sector_df = load_json_df(os.path.join(base_path, f"sina_sector_{report_date}.json"))
        concept_df = load_json_df(os.path.join(base_path, f"concept_{report_date}.json"))
        region_df = load_json_df(os.path.join(base_path, f"region_{report_date}.json"))
        industry_df = load_json_df(os.path.join(base_path, f"industry_{report_date}.json"))
        # 获取新浪行业数据
    else:
        sina_sector_df = ak.stock_sector_spot("新浪行业")
        save_to_json_v2(sina_sector_df, os.path.join(base_path, f"sina_sector_{report_date}.json"))
        # print(sina_sector_df)
        # 获取概念数据
        concept_df = ak.stock_sector_spot("概念")
        save_to_json_v2(concept_df, os.path.join(base_path, f"concept_{report_date}.json"))
        # print(concept_df)
        # 获取地域数据
        region_df = ak.stock_sector_spot("地域")
        save_to_json_v2(region_df, os.path.join(base_path, f"region_{report_date}.json"))
        # print(region_df)
        # 获取行业数据
        industry_df = ak.stock_sector_spot("行业")
        save_to_json_v2(industry_df, os.path.join(base_path, f"industry_{report_date}.json"))
        # print(industry_df)

    # 合并所有数据并提取label列
    all_data_df = pd.concat([sina_sector_df, concept_df, region_df, industry_df], ignore_index=True)
    labels = (all_data_df['label'].unique())
    # print(labels)
    # for idx, label in enumerate(labels):
    #     print(f"Index: {idx}, Label: {label}")
    # # 根据sector名称获取详细数据
    # for label in labels:
    #     sector_detail_df = ak.stock_sector_detail(sector=label)
    #     print(f"Sector: {label}")
    #     print(sector_detail_df)
    #     save_to_json_v2()
    #

    # 将label列转为字典，之后调用模板函数
    api_dict = {
        "stock_sector_detail":(ak.stock_sector_detail,{}),

    }
    for key, (func, params) in api_dict.items():
        relative_traversal_module(func, key, labels, params)





# print(ak.stock_analyst_rank_em("2023").columns)
#     # 新浪财经-股票-机构持股详情
#     "stock_institute_hold_detail": (
#     ak.stock_institute_hold_detail, {"quarter": "20241"}),   # 股票代码+查询

def stock_report_fund_hold_detail(date, symbol):
    # 取基金代码列
    df = ak.stock_fund_stock_holder(symbol)
    fund_dict = df['基金代码']
    # 在这里遍历date
    relative_traversal_module(func=ak.stock_report_fund_hold_detail,basic_name="stock_report_fund_hold_detail",
                              dict=fund_dict,args={"date":f"{date}"})
    # ak.stock_report_fund_hold_detail()



def stock_analyst_detail_em(date):
    year = datetime.strptime(date, "%Y%m%d").year

    analyst_df = ak.stock_analyst_rank_em()
    analyst_dict = analyst_df['分析师ID']
    # 取分析师ID
    # {"最新跟踪成分股", "历史跟踪成分股", "历史指数"}
    # 三个传入的func，args{"analyst_id": "11000257131", "indicator": "最新跟踪成分股"}
    # {"analyst_id": "11000257131", "indicator": "历史跟踪成分股"}
    # {"analyst_id": "11000257131", "indicator": "历史指数"}
    # ak.stock_analyst_detail_em(indicator="最新跟踪成分股")
    # ak.stock_analyst_detail_em(indicator="历史跟踪成分股")
    # ak.stock_analyst_detail_em(indicator="历史指数")
    api_dict = {
        "stock_analyst_detail_em_latest": (
            ak.stock_analyst_detail_em, {"indicator": "最新跟踪成分股"}),
        "stock_analyst_detail_em_historical": (
            ak.stock_analyst_detail_em, {"indicator": "历史跟踪成分股"}),
        "stock_analyst_detail_em_historical_index": (
            ak.stock_analyst_detail_em, {"indicator": "历史指数"}),
    }
    for key, (func, params) in api_dict.items():
        relative_traversal_module(func, key, analyst_dict, params)

def stock_sector_fund_flow_summary_and_hist(date, base_path="./stock_data/stock_relative"):
    start = datetime.strptime(date, "%Y%m%d")
    current_year = datetime.now().year
    year = start.year
    if year < current_year:
        date_str = f"{year}1231"
    elif year == current_year:
        date_str = f"{year}0331"

    dict_path = os.path.join(base_path, f"stock_sy_hy_em_{date_str}")
    stock_sy_hy_em_df = load_json_df(dict_path)
    if stock_sy_hy_em_df.empty:
        stock_sy_hy_em_df = ak.stock_sy_hy_em(date=f"{date_str}")  # 特殊日期~~~~
        if stock_sy_hy_em_df.empty:
            print(f"In stock_sector_fund_flow_summary_and_hist: Error! fail to fetch ak.stock_sy_hy_em")
            return

    dict_sector = stock_sy_hy_em_df['行业名称']

    # 取行业名称列
    # ak.stock_sector_fund_flow_summary()
    # # ak.stock_sector_fund_flow_summary, {"symbol": "电源设备", "indicator": "今日"})
    # ak.stock_sector_fund_flow_hist()
    api_dict = {
        # "stock_sector_detail": (ak.stock_sector_detail, {}),
        "stock_sector_fund_flow_summary_today": (
            ak.stock_sector_fund_flow_summary, {"indicator": "今日"}),
        "stock_sector_fund_flow_summary_5days": (
            ak.stock_sector_fund_flow_summary, {"indicator": "5日"}),
        "stock_sector_fund_flow_summary_10days": (
            ak.stock_sector_fund_flow_summary, {"indicator": "10日"}),
        # 东方财富网-数据中心-资金流向-行业资金流-行业历史资金流
        "stock_sector_fund_flow_hist": (ak.stock_sector_fund_flow_hist, {}),
    }
    for key, (func, params) in api_dict.items():
        relative_traversal_module(func, key, dict_sector, params)



def stock_concept_fund_flow_hist():
    stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
    board_name = stock_board_concept_name_em_df['板块名称']
    # 取板块名称
    api_dict={
        "stock_concept_fund_flow_hist": (ak.stock_concept_fund_flow_hist,{})
    }
    for key, (func, params) in api_dict.items():
        relative_traversal_module(func, key, board_name, params)


report_date="20240729"
stock_sector_detail(report_date)
# stock_report_fund_hold_detail(report_date, symbol)  # 要装在遍历的函数里面
stock_analyst_detail_em(report_date)
stock_sector_fund_flow_summary_and_hist(report_date)
stock_concept_fund_flow_hist()  # 获取失败









# print(ak.stock_concept_fund_flow_hist(symbol="华为欧拉"))

# 新浪行业-板块行情-成份详情 http:// finance. sina. com. cn/ stock/ sl/#area_1 :param sector: stock_sector_spot 返回的 label 值,
# choice of {"新浪行业", "概念", "地域", "行业"}; "启明星行业" 无详情 :type sector: str :return: 指定 sector 的板块详情 :rtype: pandas. DataFrame
api = {"stock_sector_detail": (ak.stock_sector_detail, {"sector": "hangye_ZL01"}),  # 遍历返回的参数ak.stock_sector_spot


# 遍历基金代码 遍历中的遍历 "stock_fund_stock_holder": (ak.stock_fund_stock_holder, {}),  # 遍历、季度 最好融合到一起
# stock_fund_stock_holder
# "stock_report_fund_hold_detail": (
#     ak.stock_report_fund_hold_detail, {"date": f"{generate_report_dates(begin_date, end_date)}"}),
# 需要获取基金代码


# 东方财富网-数据中心-龙虎榜单-个股龙虎榜详情
# symbol – 股票代码
# date – 查询日期; 需要通过 ak. stock_lhb_stock_detail_date_em(symbol="600077") 接口获取相应股票的有龙虎榜详情数据的日期
# flag – choice of {"买入", "卖出"}

"stock_lhb_stock_detail_em_buy": (ak.stock_lhb_stock_detail_em, {"symbol": "", "date": "", "flag": "买入"}),
"stock_lhb_stock_detail_em_sell": (ak.stock_lhb_stock_detail_em, {"symbol": "", "date": "", "flag": "卖出"}),

# 个股详情 # ak. stock_lhb_stock_detail_date_em(symbol="600077")

    # 东方财富网-数据中心-研究报告-东方财富分析师指数-东方财富分析师指数2020最新排行-分析师详情
    # 形参:
    # analyst_id – 分析师 ID, 从 ak. stock_analyst_rank_em() 获取
    # indicator – choice of {"最新跟踪成分股", "历史跟踪成分股", "历史指数"}
    "stock_analyst_detail_em": (
    ak.stock_analyst_detail_em, {"analyst_id": "11000257131", "indicator": "最新跟踪成分股"}),  # 分析师详情


    # # 巨潮资讯-首页-公告查询-信息披露公告  这个是遍历+简单参数 # 已获取
    # "stock_zh_a_disclosure_report_cninfo": (ak.stock_zh_a_disclosure_report_cninfo,
    #                                         {"symbol": "000001", "market": "沪深京", "category": "公司治理",
    #                                          "start_date": "20230619", "end_date": "20231220"}),  # 信息披露公告
    # # 巨潮资讯-首页-数据-预约披露调研 遍历+简单参数
    # "stock_zh_a_disclosure_relation_cninfo": (ak.stock_zh_a_disclosure_relation_cninfo,
    #                                           {"symbol": "000001", "market": "沪深京", "start_date": "20230619",
    #                                            "end_date": "20231220"}),  # 信息披露调研

    # 东方财富网-数据中心-资金流向-行业资金流-xx行业个股资金流 stock_sy_hy_em_df = ak.stock_sy_hy_em(date="20230331")
    "stock_sector_fund_flow_summary": (
        ak.stock_sector_fund_flow_summary, {"symbol": "电源设备", "indicator": "今日"}),
    # 东方财富网-数据中心-资金流向-行业资金流-行业历史资金流
    "stock_sector_fund_flow_hist": (ak.stock_sector_fund_flow_hist, {"symbol": "电源设备"}),
    # 东方财富网-数据中心-资金流向-概念资金流-概念历史资金流
    "stock_concept_fund_flow_hist": (ak.stock_concept_fund_flow_hist, {"symbol": "锂电池"}),
    # 新浪财经-股票-机构持股详情
    "stock_institute_hold_detail": (
    ak.stock_institute_hold_detail, {"quarter": "20241"}),   # 股票代码+查询
}
