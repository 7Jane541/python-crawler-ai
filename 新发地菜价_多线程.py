import requests
import json
import csv
import random
import time
from concurrent.futures import ThreadPoolExecutor
import threading

url = "http://www.xinfadi.com.cn/getPriceData.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
}
# 全局锁：多线程写csv必须用
write_lock = threading.Lock()
# 文件名称：新发地菜价_多线程.csv
csv_file = "新发地菜价_多线程.csv"


def crawl_page(page):
    """单个线程爬一页"""
    post_data = {
        "current": page,
        "limit": 20,
        "pubDateStartTime": "",
        "pubDateEndTime": "",
        "prodPcatid": "",
        "prodCatid": "",
        "prodName": ""
    }
    try:
        # 生成一个 [a, b] 区间内的随机浮点数（小数）：random.uniform(a, b)
        time.sleep(random.uniform(0.2, 0.6))
        resp = requests.post(url, json=post_data, headers=headers, timeout=10)
        res_json = resp.json()
        data_list = res_json["list"]
        print(f"✅ 线程完成第{page}页，拿到{len(data_list)}条")

        with write_lock:
            if data_list:
                with open(csv_file, "a", encoding="utf-8-sig", newline="") as f:
                    # **专门用来把字典列表写入 csv**的类。
                    writer = csv.DictWriter(f, fieldnames=data_list[0].keys())
                    writer.writerows(data_list)
        return data_list
    except Exception as e:
        print(f"❌ 第{page}页失败，错误：{e}")
        return []


if __name__ == '__main__':
    # 只请求【一次】第一页，同时拿到：总数量 + 表头样本
    post_data = {"current": 1, "limit": 20, "pubDateStartTime": "",
                 "pubDateEndTime": "", "prodPcatid": "", "prodCatid": "", "prodName": ""}
    resp = requests.post(url, json=post_data, headers=headers)
    res_json = resp.json()
    total = res_json["count"]
    sample = res_json["list"][0]

    # 计算总页数
    limit = 20
    total_page = (total + limit - 1) // limit
    print(f"总数据：{total} 条，总页数：{total_page}")

    # 写入表头
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sample.keys())
        writer.writeheader()

    # 测试：限制只爬前10页
    total_page = min(total_page, 10)

    # 线程池，4个线程
    with ThreadPoolExecutor(max_workers=4) as executor:
        pages = range(1, total_page + 1)
        # executor.map()：多线程爬取多页
        # `map`：把`pages`里面**每一个页码，依次传给 crawl_page 函数**
        executor.map(crawl_page, pages)

    print("🎉 多线程全部任务结束！")
