import csv
from lxml import etree
import requests

url = 'https://www.zbj.com/index2018/'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0"
}
# 1. 发送请求
response = requests.get(url, headers=headers)
# 2. 获取响应数据
html = response.text
# print(html)  # 打印响应数据，方便调试
# 3. 解析数据
tree = etree.HTML(html)
# 4. 提取数据
# 获取电影名称
divs = tree.xpath('/html/body/div[1]/div[6]/div[1]/div[1]/div/div/div')
import csv
all_rows = []  # 用来存最终要写进csv的数据

for div in divs:
    # 取一级分类
    text_list = div.xpath("./a/span/text()")
    text_res = [x.strip() for x in text_list[0].split("/")] if text_list else []

    # 取3个二级标签
    ls1_list = div.xpath("./p/a[1]/text()")
    ls1 = [x.strip() for x in ls1_list[0].split("/")] if ls1_list else []

    ls2_list = div.xpath("./p/a[2]/text()")
    ls2 = [x.strip() for x in ls2_list[0].split("/")] if ls2_list else []

    ls3_list = div.xpath("./p/a[3]/text()")
    ls3 = [x.strip() for x in ls3_list[0].split("/")] if ls3_list else []

    # ========== 核心：空列表直接删掉，不保留[] ==========
    valid_parts = []
    if text_res:
        valid_parts.append(text_res)
    if ls1:
        valid_parts.append(ls1)
    if ls2:
        valid_parts.append(ls2)
    if ls3:
        valid_parts.append(ls3)
    
    # 打印出来就不会再出现多余的 [] 了
    print(*valid_parts)

    # ========== 整理成csv一行 ==========
    if not text_res:  # 空条目直接跳过
        continue
    main_cate = text_res[0]  # 大分类名（比如"工商财税"）
    # 合并所有非空的子标签
    all_sub_tags = ls1 + ls2 + ls3
    all_sub_tags = [tag.strip() for tag in all_sub_tags if tag.strip()]  # 去空格、去空串
    tags_str = "、".join(all_sub_tags)  # 顿号拼接，Excel里好看

    all_rows.append([main_cate, tags_str])


# ========== 写入CSV（Excel打开不乱码） ==========
with open("website_cates.csv", "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["分类名称", "下属标签"])  # 表头
    writer.writerows(all_rows)

print("✅ CSV已保存：website_cates.csv")
