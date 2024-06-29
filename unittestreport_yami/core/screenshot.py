import tempfile
import requests


def add_screenshot_with_local(test):
    if type(getattr(test, "driver", "")).__name__ == "WebDriver":
        try:
            driver = getattr(test, "driver")
            test.images.append(driver.get_screenshot_as_base64())
        except Exception as e:
            print(f"local screenshot error! error:{e}")
            raise e


def add_screenshot_with_s3(test):
    if type(getattr(test, "driver", "")).__name__ == "WebDriver":
        response = None
        try:
            driver = getattr(test, "driver")

            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file_path = temp_file.name
                driver.save_screenshot(temp_file_path)
                response = upload_to_s3(test.s3_url, temp_file_path)
                body = response.get("body", [])
                if body:
                    url = body[0].get("url")
                    if url:
                        test.images.append(url)
        except Exception as e:
            print(f"upload screenshot to s3 error! response:{response}, error:{e}")
            raise e


def upload_to_s3(s3_url, file_path):
    files = {"file": (file_path, open(file_path, "rb"), "image/jpeg")}
    data = {"type": "common", "channel": "Yamibuy", "local": "local"}
    headers = {"token": "example-token"}

    try:
        response = requests.post(s3_url, files=files, data=data, headers=headers)
        return response.json()
    except Exception as e:
        print(f"upload screenshot to s3 error! error:{e}")
        return {}


def add_screenshot(test):
    if hasattr(test, "s3_url"):
        return add_screenshot_with_s3(test)
    return add_screenshot_with_local(test)
