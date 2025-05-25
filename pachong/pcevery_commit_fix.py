from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import json

# 读取 URL 数据
# url_data = []
# data = []
n = 0
m = 0
nn = 0
urls = []
urls2=[]
urls_link=[]

with open("commit_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 提取所有 title 的链接
for item in data:
    uuu = item.get("commit", "")
    urls2.append(uuu)

with open("merged.json", "r", encoding="utf-8") as f:
    url_data = json.load(f)

# 提取所有 title 的链接
for item in url_data:
    title_link = item.get("commit", "")
    if title_link and title_link not in urls2:
        urls.append(title_link)
        nn += 1
        link_link = item.get("link", "")
        if link_link:
            urls_link.append(link_link)
print(nn)
print(len(urls_link))

result_dict = dict(zip(urls, urls_link))

# 爬取网页内容并提取数据
def scrape_url(url):
    try:
        dist={}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)

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
            global result_dict
            url_link=result_dict[url]
            data = {
                "link": url_link,
                "commit": url,
                "commit_dist": dist
            }
            browser.close()
            global m
            m+=1
            return data

    except Exception as e:
        print(f"Error occurred while processing {url}: {e}")
        return None

def clean_and_deduplicate_json(data, key):
    # with open(input_file, 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    
    unique_data = {}  # 用字典去重，确保 key 唯一
    for item in data:
        unique_data[item[key]] = item  # 如果 key 重复，后面的会覆盖前面的
    
    return list(unique_data.values())

# 并行化爬取多个网页
with ThreadPoolExecutor(max_workers=4) as executor:  # 可以调整 max_workers 的数量
    future_to_url = {executor.submit(scrape_url, url): url for url in urls}

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