import tempfile
import requests


def add_screenshot_with_local(test):
    if type(getattr(test, "driver", "")).__name__ == "WebDriver":
        try:
            driver = getattr(test, "driver")
            test.images.append(driver.get_screenshot_as_base64())
        except Exception as e:
            print(e)
            driver.quit()


def add_screenshot_with_s3(test):
    if type(getattr(test, "driver", "")).__name__ == "WebDriver":
        try:
            driver = getattr(test, "driver")

            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file_path = temp_file.name
                driver.save_screenshot(temp_file_path)
                response = upload_to_s3(temp_file_path)
                url = response.get("body", {}).get("url")
                if url:
                    test.images.append(url)
        except Exception as e:
            print(e)
            driver.quit()


def upload_to_s3(file_path):
    url = "https://rs.yamibuy.tech/resource/upload"
    files = {"file": (file_path, open(file_path, "rb"), "image/jpeg")}
    data = {"type": "common", "channel": "Yamibuy", "local": "local"}
    headers = {"token": "example-token"}

    response = requests.post(url, files=files, data=data, headers=headers)
    return response.json()


def add_screenshot(test):
    if test.s3_image:
        return add_screenshot_with_s3(test)
    return add_screenshot_with_local(test)
