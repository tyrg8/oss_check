# # table > tbody > tr:nth-child(2)
# # table > tbody > tr:nth-child(3)
# from bs4 import BeautifulSoup
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import json
# from selenium.webdriver.common.by import By
# import re
# from bs4 import BeautifulSoup
# from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.support.ui import WebDriverWait
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import json



# # 读取 URL 数据
# url_data = []
# data = []
# n = 0
# m = 0
# nn = 0
# urls = []

# with open("merged.json", "r", encoding="utf-8") as f:
#     url_data = json.load(f)

# # 提取所有 title 的链接
# for item in url_data:
#     title_link = item.get("commit", "")
#     if title_link:
#         urls.append(title_link)
#         nn += 1
# print(nn)

# # 设置无头模式的 Chrome 浏览器
# def create_driver():
#     options = webdriver.ChromeOptions()
#     options.add_argument("--headless")  # 无头模式
#     options.add_argument("--disable-gpu")  # 禁用 GPU 加速
#     options.add_argument("--no-sandbox")  # 避免权限问题
#     options.add_argument("--disable-dev-shm-usage")  # 避免共享内存问题
#     driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
#     return driver

# # 爬取网页内容并提取数据
# def scrape_url(url):
#     try:
#         driver = create_driver()
#         driver.get(url)
#         wait = WebDriverWait(driver, 3)

#         driver.execute_script("""
#     var templates = document.querySelectorAll('template');
#     templates.forEach(function(template) {
#         if (template.content) {
#             var clone = document.importNode(template.content, true);
#             template.parentNode.replaceChild(clone, template);
#         }
#     });
# """)




#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         from selenium.webdriver.support import expected_conditions as EC
#         from selenium.webdriver.common.by import By
#         wait = WebDriverWait(driver, 10)
#         # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "dom-repeat")))
#         wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "template")))
#         wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table > tbody > tr")))
#         # # print(driver.page_source)
        
#         # with open("try.html", "w", encoding="utf-8") as file:
#         #     file.write(driver.page_source)




#         dist={}
        
#         soup = BeautifulSoup(driver.page_source, "html.parser")

#         # pp=soup.select_one("table > tbody > tr.title > td:nth-child(1) > span")
#         # if pp:
#         #     print(f"aaa{pp.decode_contents()}")
#         # else:
#         #     print("未找到指定元素")

#         # rows = soup.select("table > tbody")
#         # driver.execute_script("document.querySelector('template').shadowRoot.querySelector('dom-repeat').render();")
#         rows = driver.find_elements(By.CSS_SELECTOR, "table > tbody > tr")
#         for tr in rows:
#             print(tr.get_attribute("outerHTML")) 
#             # soup = BeautifulSoup(row.get_attribute("innerHTML"), "html.parser")
#             # text_content = soup.get_text("\n", strip=True) 

#         tbody = soup.select_one("table > tbody")
#         rows = tbody.find_all("tr")
#         print(len(rows))
#         for row in rows:
#             component,revision = row.select('td')
#             if component:
#                 c_s=component.select_one("span")
#                 component_str = ""
#                 if c_s:
#                     component_str = c_s.decode_contents()
#             if revision:
#                 r_a=revision.select_one("if-else > span:nth-child(1) > a")
#                 revision_str = ""
#                 if r_a:
#                     revision_str = r_a.get('href')
#                 dist[component_str] = revision_str

#         data = {
#             "commit": url,
#             "commit_dist": dist
#         }
            
#         # print(data)
#         # print("\n------\n")

#         global m
#         m+=1
#         return data

#     except Exception as e:
#         print(f"Error occurred while processing {url}: {e}")
#         return None

# print(scrape_url("https://oss-fuzz.com/revisions?job=libfuzzer_ubsan_libpng-proto&range=202409070645:202409080650"))

# # # 并行化爬取多个网页
# # with ThreadPoolExecutor(max_workers=4) as executor:  # 可以调整 max_workers 的数量
# #     future_to_url = {executor.submit(scrape_url, url): url for url in urls}

# #     for future in as_completed(future_to_url):
# #         url_data = future.result()
# #         if url_data:
# #             data.append(url_data)
# #             with open("commit_data.json", "w", encoding="utf-8") as file:
# #                 json.dump(data, file, ensure_ascii=False, indent=4)
# #             n += 1
# #             print(f"-------------{m}/{n}/{nn}, finish--------------")

# # print("数据已保存到 commit_data.json 文件中")



from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import json



# 读取 URL 数据
url_data = []
data = []
n = 0
m = 0
nn = 0
urls = []
urls_link=[]

with open("merged.json", "r", encoding="utf-8") as f:
    url_data = json.load(f)

# 提取所有 title 的链接
for item in url_data:
    title_link = item.get("commit", "")
    if title_link:
        urls.append(title_link)
        nn += 1
print(nn)

for item in url_data:
    title_link = item.get("link", "")
    if title_link:
        urls_link.append(title_link)
print(len(urls_link))

result_dict = dict(zip(urls_link, urls))

def scrape_url(url):
    try:
        dist={}
        global result_dict
        url_commit=result_dict[url]
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url_commit)

            # 等待 <tr class="body"> 元素渲染完成
            page.wait_for_selector('table > tbody > tr.body')

            # 获取所有 tr.body 元素的文本内容
            rows = page.query_selector_all('table > tbody > tr.body')
            for row in rows:
                component,revision = row.query_selector_all('td')
                c = component.query_selector('span')
                c_str=""
                r_str=""
                if c:
                    c_str = c.inner_text()
                    # print(c_str)
                r = revision.query_selector('if-else > span:nth-child(1) > a')
                if r:
                    r_str = r.get_attribute('href')
                    # print(r_str)
                dist[c_str] = r_str
            data = {
                "link": url,
                "commit": url_commit,
                "commit_dist": dist
            }
            browser.close()
            global m
            m+=1
            return data

    except Exception as e:
        print(f"Error occurred while processing {url}: {e}")
        return None
# print(scrape_url("https://oss-fuzz.com/revisions?job=libfuzzer_ubsan_libpng-proto&range=202409070645:202409080650"))

def clean_and_deduplicate_json(data, key):
    # with open(input_file, 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    
    unique_data = {}  # 用字典去重，确保 key 唯一
    for item in data:
        unique_data[item[key]] = item  # 如果 key 重复，后面的会覆盖前面的
    print(len(list(unique_data.values())))
    return list(unique_data.values())

with ThreadPoolExecutor(max_workers=4) as executor:  # 可以调整 max_workers 的数量
    future_to_url = {executor.submit(scrape_url, url): url for url in urls_link}

    for future in as_completed(future_to_url):
        url_data = future.result()
        if url_data:
            data.append(url_data)
            with open("commit_data.json", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            n += 1
            print(f"-------------{m}/{n}/{nn}, finish--------------")

with open("commit_data.json", "w", encoding="utf-8") as file:
    json.dump(clean_and_deduplicate_json(data,"link"), file, ensure_ascii=False, indent=4)

print("数据已保存到 commit_data.json 文件中")
