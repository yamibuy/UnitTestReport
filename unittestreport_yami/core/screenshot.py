import tempfile
import requests
import os


def add_screenshot_with_local(test):
    driver = getattr(test, "driver")
    if driver:
        try:
            driver = getattr(test, "driver")
            test.images.append(driver.get_screenshot_as_base64())
        except Exception as e:
            print(f"local screenshot error! error:{e}")
            raise e


def add_screenshot_with_s3(test):
    driver = getattr(test, "driver")
    if driver:
        temp_file_path = ""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file_path = temp_file.name
            driver.save_screenshot(temp_file_path)
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
            if body:
                url = body[0].get("url")
        except Exception as e:
            print(f"upload screenshot to s3 error! error:{e}")
    os.remove(file_path)
    return url


def add_screenshot(test):
    if hasattr(test, "s3_url"):
        return add_screenshot_with_s3(test)
    return add_screenshot_with_local(test)
