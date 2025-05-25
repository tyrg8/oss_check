# https://issues.oss-fuzz.com/issues?q=verified%3C2024-10-01%20type:(bug%20%7C%20vulnerability)%20verified%3E2024-08-01
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

url_fix="https://issues.oss-fuzz.com"
url="https://issues.oss-fuzz.com/issues?q=verified%3C2024-10-01%20type:(bug%20%7C%20vulnerability)%20verified%3E2024-08-01"
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
driver.get(url)
# wait = WebDriverWait(driver, 3)

# 等待并点击下拉菜单按钮
wait = WebDriverWait(driver, 10)
dropdown_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Results per page')]")))
dropdown_button.click()
time.sleep(1)  # 确保动画完成

# 选择 "250" 选项
option_250 = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '250')]")))
option_250.click()

# 等待表格刷新
time.sleep(5)  # 可用 WebDriverWait 替代，但 sleep 更稳妥

SCROLL_PAUSE_TIME = 2

# 滚动到底部以加载所有内容
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)  # 等待加载
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break  # 没有新内容加载，停止滚动
    last_height = new_height


data = []

page_num = 1
while True:
    # 保存当前页数据
    # 获取完整的 HTML
    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select('#skiplink-navigation-target > list-issues-page > div.bv2-view > div > b-issues-grid > div > mat-sidenav-container > mat-sidenav-content > pop-grid > table > tbody > tr')
    print(f"页数：{page_num}；条目数：{len(rows)}")
    # 处理每一行
    for row in rows:
        row_data = {}
        td_url = row.select_one('td[data-template="issueId"] a')
        if td_url:
            row_data["link"] = url_fix+"/"+td_url.get('href')
            row_data["tittle"] = td_url.get('title')
        td_status = row.select_one('td[data-stable-cell="status"] span span')
        if td_status:
            row_data["status"] = td_status.get_text(strip=True)
        td_type = row.select_one('td[data-stable-cell="type"]')
        if td_type:
            row_data["type"] = td_type.get_text(strip=True)
        data.append(row_data)

    # 查找 "下一页" 按钮
    try:
        next_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Go to next page')]")

        # 检查是否“可点击”（有些网站到最后一页后，按钮仍然存在但不可用）
        if "disabled" in next_button.get_attribute("class") or not next_button.is_enabled():
            print("到达最后一页，爬取结束！")
            break

        # 点击 "下一页" 按钮
        next_button.click()
        page_num += 1

        # 等待新页面加载
        time.sleep(5)

    except:
        print("没有找到“下一页”按钮，爬取结束！")
        break

# 关闭 WebDriver
driver.quit()

with open("table_data.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4) 
    print(f"{len(data)}条数据已保存到table_data.json 文件中")


# # 获取完整的 HTML
# soup = BeautifulSoup(driver.page_source, "html.parser")

# # # 保存 HTML 文件
# # with open("page.html", "w", encoding="utf-8") as file:
# #     file.write(soup.prettify()) 
# #     print("数据已保存到page.html文件中")


# rows = soup.select('#skiplink-navigation-target > list-issues-page > div.bv2-view > div > b-issues-grid > div > mat-sidenav-container > mat-sidenav-content > pop-grid > table > tbody > tr')
# print(len(rows))
# data = []
#     # 处理每一行
# for row in rows:
#     row_data = {}
#     td_url = row.select_one('td[data-template="issueId"] a')
#     if td_url:
#         row_data["link"] = url_fix+"/"+td_url.get('href')
#         row_data["tittle"] = td_url.get('title')
#     td_status = row.select_one('td[data-stable-cell="status"] span span')
#     if td_status:
#         row_data["status"] = td_status.get_text(strip=True)
#     td_type = row.select_one('td[data-stable-cell="type"]')
#     if td_type:
#         row_data["type"] = td_type.get_text(strip=True)
#     data.append(row_data)
# with open("table_data.json", "w", encoding="utf-8") as file:
#     json.dump(data, file, ensure_ascii=False, indent=4) 
#     print("数据已保存到table_data.json 文件中")