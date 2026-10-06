from openai import OpenAI
import pandas as pd

# 这个就是你网页上的compatible的地址，直接复制
client = OpenAI(
    api_key="api_key_here",
    base_url="https://ws-87lzfmp5psk8ssyu.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
)

# 3. 准备你要发给 AI 的数据（这里模拟你爬到的电影数据）
df = pd.read_csv("csv/新发地菜价_多线程.csv", encoding="utf-8-sig")
菜价数据 = df.head(20).to_string(index=False)
# 4. 写提示词（Prompt）
提示词 = f"这是今天新发地的菜价数据：\n{菜价数据}。\n请帮我用200个字左右，写一份简短的菜价波动报告。"
try:
    # 5. 调用接口，获取AI的回答
    resp = client.chat.completions.create(
        model="qwen-flash",
        messages=[{"role":"user","content":提示词}], # 这里是提示词
    )
    print(resp.choices[0].message.content)
except Exception as e:
    print(f"请求AI接口失败: {e}")

