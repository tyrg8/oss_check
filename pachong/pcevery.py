from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from selenium.webdriver.common.by import By
import re
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from concurrent.futures import ThreadPoolExecutor, as_completed
import json



# 读取 URL 数据
url_data = []
data = []
n = 0
m = 0
nn = 0
urls = []

with open("table_data.json", "r", encoding="utf-8") as f:
    url_data = json.load(f)

# 提取所有 title 的链接
for item in url_data:
    title_link = item.get("link", "")
    if title_link:
        urls.append(title_link)
        nn += 1
print(nn)

# 设置无头模式的 Chrome 浏览器
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 无头模式
    options.add_argument("--disable-gpu")  # 禁用 GPU 加速
    options.add_argument("--no-sandbox")  # 避免权限问题
    options.add_argument("--disable-dev-shm-usage")  # 避免共享内存问题
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver

# 爬取网页内容并提取数据
def scrape_url(url):
    try:
        driver = create_driver()
        driver.get(url)
        wait = WebDriverWait(driver, 3)
        # 选择目标元素
        comment_divs = driver.find_elements(By.CSS_SELECTOR, "#comment1 > div > b-note-container > div > div > b-formatted-comment-presenter > b-plain-format-presenter > div > b-plain-format-section > b-plain-format-unquoted-section > div")
        
        for div in comment_divs:
            soup = BeautifulSoup(div.get_attribute("innerHTML"), "html.parser")
            text_content = soup.get_text("\n", strip=True)  # 只保留文本和链接，保持缩进和换行
            
            data = {
                "link": url,
                "text": text_content,
                "commit": None,
                "testcase": None,
                "project": None,
                "target": None
            }
            
            # 提取 commit 和 testcase 链接
            commit_match = re.search(r"(https://oss-fuzz.com/revisions[^\s]+)", text_content)
            testcase_match = re.search(r"(https://oss-fuzz.com/download[^\s]+)", text_content)
            
            if commit_match:
                data["commit"] = commit_match.group(1)
            if testcase_match:
                data["testcase"] = testcase_match.group(1)
            
            # 提取 project 和 target
            project_match = re.search(r"Project: (.+?)\n", text_content)
            target_match = re.search(r"Fuzz Target: (.+?)\n", text_content)
            
            if project_match:
                data["project"] = project_match.group(1).strip()
            if target_match:
                data["target"] = target_match.group(1).strip()
            
            # print(data)
            # print("\n------\n")

            global m
            m+=1
            return data

    except Exception as e:
        print(f"Error occurred while processing {url}: {e}")
        return None

# 并行化爬取多个网页
with ThreadPoolExecutor(max_workers=4) as executor:  # 可以调整 max_workers 的数量
    future_to_url = {executor.submit(scrape_url, url): url for url in urls}

    for future in as_completed(future_to_url):
        url_data = future.result()
        if url_data:
            data.append(url_data)
            with open("report_data.json", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            n += 1
            print(f"-------------{m}/{n}/{nn}, finish--------------")

print("数据已保存到 report_data.json 文件中")