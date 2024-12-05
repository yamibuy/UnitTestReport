import tempfile
import requests
import os
from PIL import Image
import io


def add_screenshot_with_local(test):
    driver = getattr(test, "driver", None)
    if driver:
        try:
            driver = getattr(test, "driver")
            test.images.append(driver.get_screenshot_as_base64())
        except Exception as e:
            print(f"local screenshot error! error:{e}")
            raise e


def add_screenshot_with_s3(test):
    driver = getattr(test, "driver", None)
    if driver:
        temp_file_path = ""
        # 创建临时文件，使用.webp后缀
        with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_dir = os.path.dirname(temp_file_path)
            
            # 检查目录下的图片数量
            image_count = sum(1 for f in os.listdir(temp_dir) if f.lower().endswith(('.webp', '.png')))
            if image_count >= 10000:
                print(f"警告：目录 {temp_dir} 中的图片数量已达到{image_count}张，超过限制，不再保存新的截图")
                return
                
            # 获取截图为PNG格式的二进制数据
            png_data = driver.get_screenshot_as_png()
            # 在内存中用PIL处理图片
            img = Image.open(io.BytesIO(png_data))
            # 转换为WebP格式并保存，quality参数范围是0-100，可以根据需要调整
            img.save(temp_file_path, format='WEBP', quality=30, method=6)
            # # 获取并打印文件大小
            # file_size = os.path.getsize(temp_file_path)
            # print(f"WebP格式截图大小: {file_size/1024/1024:.2f}MB ({file_size/1024:.2f}KB)")
            test.images.append(temp_file_path)


def upload_to_s3(s3_url, file_path):
    url = ""
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "image/jpeg")}
        data = {"type": "common", "channel": "Yamibuy", "local": "local"}
        headers = {"token": "example-token"}
        try:
            response = requests.post(s3_url, files=files, data=data, headers=headers)
            body = response.json().get("body", [])
            print(f"upload screenshot to s3 scuccess! :{file_path}")
            if body:
                url = body[0].get("url")
        except Exception as e:
            print(f"upload screenshot to s3 error! error:{e}")
    os.remove(file_path)
    return url


def add_screenshot(test):
    try:
        if hasattr(test, "s3_url"):
            return add_screenshot_with_s3(test)
        return add_screenshot_with_local(test)
    except Exception as e:
        print(f"add screenshot error! error:{e}")
