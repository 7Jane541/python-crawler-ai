"""
思路：
    1.拿到页面源代码，找到iframe
    2.拿到iframe的video src,m3u8
    3.下载m3u8文件，第二层mixed.m3u8
    4.下载视频  如果有#EXT-X-KEY，这个需要解密，幸运我第一次不需要哦
    5.下载ts文件，合并ts文件
"""

from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs

# https://www.919d.com/vod/detail/id/192838.html


def get_html(target_url):
    m3u8_urls = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            # 只创建page，不再额外new_context
            page = browser.new_page()

            # 反自动化检测脚本，页面加载前注入
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """)

            # =========【重点！先注册监听事件，再打开网页】=========
            def on_request(request):
                req_url = request.url
                if ".m3u8" in req_url:
                    m3u8_urls.append(req_url)
                    print(f"🎯抓到m3u8原始地址: {req_url}")

            page.on("request", on_request)

            # 访问网页，等待网络空闲，比time.sleep更智能
            page.goto(target_url, wait_until="networkidle", timeout=60*1000)
            # 再多给几秒，等待视频播放器发起请求
            page.wait_for_timeout(5000)

            browser.close()

        if not m3u8_urls:
            print("❌没有捕获到任何m3u8链接")
            return None

        print("\n全部抓到的m3u8列表：")
        for idx, u in enumerate(m3u8_urls):
            print(idx, u)

        # 找到带?url=的中转链接
        for u in m3u8_urls:
            if "?url=" in u:
                parsed = urlparse(u)
                query_dict = parse_qs(parsed.query)
                real_m3u8 = query_dict["url"][0]
                break
        else:
            print("❌没有找到url参数里的m3u8")
            return None

        print(f"\n✅提取出来真实源站m3u8：{real_m3u8}")
        with open("m3u8-1.txt", "w", encoding="utf-8") as f:
            f.write(real_m3u8)

            print("🎉已经写入 m3u8‑1.txt")
            return real_m3u8

    except Exception as e:
        print("❌请求页面失败：", e)
        return None


if __name__ == '__main__':
    url = "文件地址"
    get_html(url)
