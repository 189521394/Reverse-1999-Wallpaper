import os
import concurrent.futures
from PIL import Image

# 1. 基础配置
SOURCE_DIR = "singlebg"
OUTPUT_DIR = "thumbnails"
MAX_SIZE = (600, 600)

# 定义单个图片的处理任务（这个函数会被分配给不同的 CPU 核心同时执行）
def process_single_image(source_path, target_path):
    # 防重复检查
    if os.path.exists(target_path):
        return "skipped"

    try:
        # 确保目标文件夹存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        with Image.open(source_path) as img:
            if img.mode in ("P", "LA"):
                img = img.convert("RGBA")

            img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)

            # 💡 极客提示：method=6 是 WebP 压缩率最高但也最耗时的算法。
            # 如果你开启了多进程还是觉得慢，可以把它改成 method=4（默认值），速度会飙升，体积只大一丁点。
            img.save(target_path, format="WEBP", quality=80, method=6)

        return "success"
    except Exception as e:
        return f"error: {source_path} - {e}"

def compress_images():
    print(f"🚀 开始执行 WebP 压缩任务...")

    tasks = [] # 任务清单

    # 遍历获取所有需要处理的路径对
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.lower().endswith('.png'):
                source_path = os.path.join(root, file)
                rel_path = os.path.relpath(source_path, SOURCE_DIR)
                rel_path_webp = rel_path[:-4] + ".webp"
                target_path = os.path.join(OUTPUT_DIR, SOURCE_DIR, rel_path_webp)

                # 把原路径和目标路径打包塞进任务清单
                tasks.append((source_path, target_path))

    # 统计数据
    success_count = 0
    skip_count = 0
    error_count = 0

    # 获取你电脑的真实 CPU 核心数
    max_workers = os.cpu_count() or 4
    print(f"使用核心： {max_workers}")

    # 多进程线程池！
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 把任务分发给各个核心
        futures = [executor.submit(process_single_image, src, tgt) for src, tgt in tasks]

        # 实时收集处理结果
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result == "success":
                success_count += 1
                # 打印进度，用回车符 \r 覆盖上一行，保持控制台整洁
                print(f"\r⚡ 已压缩: {success_count} | 已跳过: {skip_count}", end="", flush=True)
            elif result == "skipped":
                skip_count += 1
                print(f"\r⚡ 已压缩: {success_count} | 已跳过: {skip_count}", end="", flush=True)
            else:
                error_count += 1
                print(f"\n❌ {result}")

    print(f"\n\n🎉 任务完成！")
    print(f"✅ 本次新压缩: {success_count} 张")
    print(f"⏭️ 直接跳过: {skip_count} 张")
    if error_count > 0:
        print(f"❌ 失败报错: {error_count} 张")

# 多进程在 Windows 下必须要有这行入口保护，否则会无限套娃报错
if __name__ == "__main__":
    compress_images()