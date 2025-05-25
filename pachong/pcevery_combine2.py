# import json

# # 读取JSON文件
# with open('merged.json', 'r', encoding='utf-8') as f1, open('commit_data.json', 'r', encoding='utf-8') as f2:
#     json1 = json.load(f1)
#     print(len(json1))
#     json2 = json.load(f2)
#     print(len(json2))

# # 创建一个字典用于合并，key 是 link，value 是合并后的字典
# merged_dict = {}

# # 处理第一个 JSON 文件
# for item in json1:
#     link = item.get('commit')
#     if link:
#         if link not in merged_dict:
#             merged_dict[link] = item
#         else:
#             merged_dict[link].update(item)  # 合并相同 link 的字典

# # 处理第二个 JSON 文件
# for item in json2:
#     link = item.get('commit')
#     if link:
#         if link not in merged_dict:
#             merged_dict[link] = item
#         else:
#             merged_dict[link].update(item)

# # 转换回列表格式
# merged_list = list(merged_dict.values())

# print(len(merged_list))

# # 将合并后的结果保存到新文件
# with open('final.json', 'w', encoding='utf-8') as f:
#     json.dump(merged_list, f, ensure_ascii=False, indent=4)

# print("合并完成，结果已保存到 final.json")

import json

def merge_json_files(file1, file2, output_file, key):
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        data1 = json.load(f1)
        print(len(data1))
        data2 = json.load(f2)
        print(len(data2))
    
    merged_data = {}
    data2_dict = {item[key]: item for item in data2}  # 预处理 data2 以便快速查找
    
    for item in data1:
        if item[key] in data2_dict:
            merged_item = {**item, **data2_dict[item[key]]}  # 只合并成功匹配的项
            merged_data[item[key]] = merged_item
    
    print(len(merged_data))
    with open(output_file, 'w', encoding='utf-8') as out:
        json.dump(list(merged_data.values()), out, ensure_ascii=False, indent=4)

# 示例调用
merge_json_files('commit_data.json', 'merged.json', 'final.json', 'link')