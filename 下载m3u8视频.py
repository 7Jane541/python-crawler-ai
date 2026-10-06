import subprocess
import os
import asyncio
import aiohttp
import aiofiles
from urllib.parse import urljoin
import glob

SEMAPHORE = asyncio.Semaphore(15)


def read_episode_m3u8_file(file_path="m3u8-1.txt"):
    ep_list = []
    if not os.path.exists(file_path):
        print(f"❌找不到文件 {file_path}，请确认playwright已经抓取链接并保存到此文件！")
        return ep_list
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                ep_list.append(line)
    print(f"✅从文件读取到 {len(ep_list)} 个剧集m3u8链接")
    return ep_list


async def parse_m3u8_auto(input_m3u8_url):
    """自动识别一级/二级嵌套m3u8"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(input_m3u8_url) as resp:
                text = await resp.text()
                sub_m3u8 = None
                for line in text.splitlines():
                    line = line.strip()
                    if not line.startswith("#"):
                        if line.endswith(".m3u8"):
                            sub_m3u8 = urljoin(input_m3u8_url, line)
                            break
                if sub_m3u8 is not None:
                    print(f"🔍检测到二级嵌套m3u8，跳转子m3u8: {sub_m3u8}")
                    return sub_m3u8
                else:
                    print(f"🔍检测为一级m3u8，直接使用该地址")
                    return input_m3u8_url
    except Exception as e:
        print(f"parse_m3u8_auto异常：{e}")
        return None


async def get_ts_urls(final_m3u8_url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(final_m3u8_url) as resp:
                m3u8_content = await resp.text()
                ts_urls = []
                for line in m3u8_content.splitlines():
                    line = line.strip()
                    if not line.startswith('#'):
                        ts_url = urljoin(final_m3u8_url, line)
                        ts_urls.append(ts_url)
                return ts_urls
    except Exception as e:
        print("解析m3u8获取ts列表异常:", e)
        return None


async def single_download(session, ts_url, index, save_dir="ts_files"):
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    ori_name = os.path.basename(ts_url)
    ts_name = f"{index}_{ori_name}"
    save_path = os.path.join(save_dir, ts_name)
    async with SEMAPHORE:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "地址"
            }
            async with session.get(ts_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    async with aiofiles.open(save_path, "wb") as f:
                        await f.write(data)
                    print(f"✅[{index}] 下载成功 {ts_name}")
                    return True
                else:
                    print(f"❌[{index}] 状态码错误 {resp.status} {ts_url}")
                    return False
        except Exception as e:
            print(f"❌[{index}] 下载异常【类型：{type(e).__name__}】: {e}")
            return False


async def download_ts(ts_urls, ep_num, series_name):
    out_video = f"{series_name}_第{ep_num}集.mp4"
    results = [None] * len(ts_urls)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, url in enumerate(ts_urls):
            task = single_download(session, url, idx)
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        success_count = sum(results)
        fail_count = len(results) - success_count
        print(f"✅下载成功：{success_count} 个，❌下载失败：{fail_count} 个")
        if fail_count > 0:
            print("⚠️ 有分片下载失败，合并出来的视频会缺片段！")
            return False

    print("\n✅全部分片下载任务结束，开始合并视频")
    ts_dir = "ts_files"
    filelist = os.path.join(ts_dir, "filelist.txt")
    with open(filelist, "w", encoding="utf-8") as f:
        for index, url in enumerate(ts_urls):
            ori_name = os.path.basename(url)
            fn = f"{index}_{ori_name}"
            f.write(f"file '{fn}'\n")

    cmd = [
        "ffmpeg",
        "-f", "concat",
        # "-y",   # 💰 启用自动覆盖，批量跑连续剧的时候把注释#删掉；单机测试可以注释掉，手动确认
        "-safe", "0",
        "-i", "filelist.txt",
        "-c", "copy",
        f"../{out_video}"
    ]
    p = subprocess.run(cmd, cwd=ts_dir)
    if p.returncode == 0:
        print(f"🎉【第{ep_num}集】合并完成！输出文件：{out_video}")
        # 【增加try‑except容错，文件不存在也不会崩溃】
        ts_all = glob.glob(os.path.join(ts_dir, "*.ts"))
        for fpath in ts_all:
            try:
                os.remove(fpath)
            except OSError:
                pass
        try:
            os.remove(filelist)
        except OSError:
            pass
        print(f"🧹【第{ep_num}集】分片文件清理完毕，准备下一集")
    else:
        print(f"⚠️【第{ep_num}集】ffmpeg合并失败，请检查！")


async def main():
    series_name = "洪水之后第一季"  # 视频名称
    ep_m3u8_list = read_episode_m3u8_file("m3u8-1.txt")
    if len(ep_m3u8_list) == 0:
        print("❌没有读到任何剧集链接，程序退出！")
        return

    for ep_idx, m3u8_link in enumerate(ep_m3u8_list, start=1):
        video_name = f"{series_name}_第{ep_idx}集.mp4"
        if os.path.exists(video_name):
            print(
                f"\n==================== 【第{ep_idx}集】{video_name} 已存在，直接跳过 ====================")
            continue

        print(f"\n==================== 开始处理【第{ep_idx}集】 ====================")
        final_m3u8 = await parse_m3u8_auto(m3u8_link)
        if not final_m3u8:
            print(f"❌【第{ep_idx}集】解析m3u8失败，跳过本集")
            continue
        ts_urls = await get_ts_urls(final_m3u8)
        if not ts_urls or len(ts_urls) == 0:
            print(f"❌【第{ep_idx}集】没有拿到ts分片，跳过")
            continue
        print(f"✅【第{ep_idx}集】一共获取到 {len(ts_urls)} 个ts分片")
        await download_ts(ts_urls, ep_idx, series_name)


if __name__ == '__main__':
    asyncio.run(main())
