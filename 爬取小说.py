import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
import re

SEMAPHORE = asyncio.Semaphore(5)  # 最大并发5个请求
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0"
}


async def fetch(session, url):
    async with SEMAPHORE:
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')  # 换成内置解析器，不用装lxml
                article = soup.find(
                    "article", class_="reading-content chapter-content-font")
                if article:
                    return article.get_text(strip=True, separator='\n')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None


async def get_catalog(session):
    """获取目录页面的所有章节链接"""
    catalog_url = 'https://xiyouji.5000yan.com/'
    async with session.get(catalog_url, headers=headers) as resp:
        html = await resp.text()
        soup = BeautifulSoup(html, 'html.parser')
        a_list = soup.find_all('a', class_='category-link')
        chapters = []
        for a in a_list:
            title = a.get_text(strip=True)
            link = a["href"]
            chapters.append((title, link))
        return chapters

# 简单清洗文件名，去掉Windows不允许的字符


def safe_filename(name):
    invalid_chars = r'\/:*?"<>|'
    for c in invalid_chars:
        name = name.replace(c, "")
    return name


def get_chapter_number(title_text):
    match = re.search(r"第(\d+)回", title_text)
    if match:
        return int(match.group(1))
    return 9999


async def main(address):
    # 自动创建文件夹
    os.makedirs(address, exist_ok=True)
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # 1.获取目录
        chapters = await get_catalog(session)
        chapters.sort(key=lambda x: get_chapter_number(x[0]))
        print(f"一共抓取了{len(chapters)}章")

        # 批量创建任务
        tasks = []
        for title, url in chapters:
            tasks.append(fetch(session, url))

        # 并发执行所有任务
        results = await asyncio.gather(*tasks)

        # 循环保存
        for (title, _), content in zip(chapters, results):
            if content:
                name = safe_filename(title) + ".txt"
                fname = os.path.join(address, name)
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"已保存：{title}")
            else:
                print(f"!!!抓取失败：{title}")
    print('全部完成！！！ ')

if __name__ == '__main__':
    address = "python爬虫/西游记"
    asyncio.run(main(address))
    print('全部完成！！！ ')
