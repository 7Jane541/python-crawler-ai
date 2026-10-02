import qrcode

# 1. 准备你要放进二维码里的内容（可以是网址，也可以是一段文字）
# 例如你的 GitHub 项目链接
content = "https://github.com/7Jane541/python-crawler-ai"

# 2. 创建二维码对象
qr = qrcode.QRCode(
    version=1,  # 控制二维码大小，1是最小，数字越大存得越多
    box_size=10, # 每个小方块的像素大小
    border=4,    # 二维码四周的留白
)
qr.add_data(content)
qr.make(fit=True)

# 3. 生成图片并保存
img = qr.make_image(fill_color="black", back_color="white")
img.save("我的二维码.png")

print("二维码生成成功！扫一下试试看！")