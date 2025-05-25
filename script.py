import os
import json
import requests
import os
import shutil
import stat
import subprocess
from urllib.parse import urlparse
# 5.7过期
token = "your_token"
# 获取上n个commit
def get_previous_commits(commit_url: str, n: int, token: str = None):
    m = re.match(r'https://github.com/([^/]+)/([^/]+)/commit/([a-f0-9]+)', commit_url)
    if not m:
        raise ValueError("提交链接格式不正确")
    owner, repo, sha = m.groups()

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    result = []
    current_sha = sha

    for _ in range(n):
        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{current_sha}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"请求失败: {resp.status_code}, {resp.text}")
        commit_data = resp.json()
        parents = commit_data.get("parents", [])
        if not parents:
            break  # 没有更多的 parent（可能到了最早的 commit）
        current_sha = parents[0]["sha"]
        result.append(current_sha)

    return result

# 读取JSON文件
with open("final.json", 'r', encoding='utf-8') as f:
    data = json.load(f)
base_dir="data"
os.makedirs(base_dir, exist_ok=True)

print(len(data))

def create_folder_and_download(item):
    folder_name = item.get("link").split('/')[-1]
    file_url = item.get("testcase")
    
    if not folder_name or not file_url:
        print(f"跳过无效项: {item}")
        return
    
    # 创建文件夹
    folder_path = os.path.join(base_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    # 获取文件名
    # file_name = os.path.basename(file_url)
    file_name = f"testcase_{folder_name}"
    file_path = os.path.join(folder_path, file_name)
    
    # 下载文件
    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        print(f"下载完成: {file_path}")
    except requests.RequestException as e:
        print(f"下载失败: {file_url}, 错误: {e}")




def extract_commit_hashes(url):
    """从 GitHub 比较 URL 中提取两个提交哈希"""
    parsed_url = urlparse(url)
    parts = parsed_url.path.split('/')  # 解析 URL 路径
    if "compare" in parts:
        hashes = parts[-1].split("...")
        if len(hashes) == 2:
            return hashes[0], hashes[1]
    return None, None

def clone_or_pull_repo(repo_url, repo_path):
    """克隆仓库或拉取最新代码"""
    if os.path.exists(repo_path):
        print("[+] 仓库已存在，执行 git pull")
        subprocess.run(["git", "-C", repo_path, "pull"], check=True)
    else:
        print("[+] 克隆仓库")
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)

def get_modified_files(repo_path, old_commit, new_commit):
    try:
        """获取两个提交之间修改的文件列表"""
        result = subprocess.run(
            ["git", "-C", repo_path, "diff", "--name-only", old_commit, new_commit],
            capture_output=True, text=True, check=True
        )
        return result.stdout.splitlines()
    except:
        print("[+] 由于未知错误无法比较两个提交")
        return []

def save_old_version_files(repo_path, modified_files, output_dir, old_commit):
    """保存旧版本的修改文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    for file in modified_files:
        save_path = os.path.join(output_dir, file)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            # 使用 git show 获取旧版本的文件内容
            result = subprocess.run(
                ["git", "-C", repo_path, "show", f"{old_commit}:{file}"],
                capture_output=True, text=True, check=True
            )
            
            # 将旧版本的内容写入文件
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(result.stdout)
                
            print(f"[+] 旧版本文件已保存: {file} -> {save_path}")
        
        except subprocess.CalledProcessError:
            print(f"[!] 文件 {file} 在提交 {old_commit} 中不存在，跳过")
            return False
    return True
def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)
def delete_path(path):
    """删除文件夹（解决权限问题）"""
    if os.path.exists(path):
        shutil.rmtree(path, onerror=remove_readonly)
        print(f"[+] 已成功删除文件夹: {path}")
def delete_path_sudo_cmd(path):
    """使用 sudo rm -rf 删除文件夹"""
    if os.path.exists(path):
        subprocess.run(["sudo", "rm", "-rf", path], check=True)
        print(f"[+] 已成功sudo rm -rf删除文件夹: {path}")

def get_diff(item):
    folder_name = item.get("link").split('/')[-1]
    folder_path = os.path.join(base_dir, folder_name)

    commit_dist = item.get("commit_dist")
    module_name, compare_url = next(iter(commit_dist.items()))

    if "/compare/" not in compare_url:
        # 删除git文件夹
        print("[！！]删除git文件夹[！！]")
        delete_path(folder_path)

        tittle = item.get("tittle")
        status = item.get("status")
        type = item.get("type")
        module = item.get("project")
        target = item.get("target")
        folder_name = item.get("link").split('/')[-1]

        commit_dist = item.get("commit_dist")
        module_name, compare_url = next(iter(commit_dist.items()))
        log_file = os.path.join(base_dir, f"{folder_name}.log")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"tittle:{tittle}\nstatus:{status}\ntype:{type}\ncompare_url:{compare_url}\nmodule:{module}\ntarget:{target}\n")
            f.write("no compare form!")
            f.write("\n" + "=" * 50 + "\n")
        return []


    repo_url = compare_url.split("/compare/")[0]+".git"
    repo_path = compare_url.split("/compare/")[0].split("/")[-1]+"_repo"
    output_dir_0 = "modified_files_old_"+compare_url.split("/compare/")[0].split("/")[-1]
    file_path_0 = "file_path_"+compare_url.split("/compare/")[0].split("/")[-1]+".txt"

    output_dir = os.path.join(folder_path, output_dir_0)
    file_path = os.path.join(folder_path, file_path_0)

    # 提取两个提交哈希
    old_commit, new_commit = extract_commit_hashes(compare_url)
    if not old_commit or not new_commit:
        print("[-] 无法解析提交哈希")
        return

    print(f"[+] 比较提交: {old_commit} -> {new_commit}")

    # 克隆或更新仓库
    clone_or_pull_repo(repo_url, repo_path)

    # 获取修改的文件
    modified_files = get_modified_files(repo_path, old_commit, new_commit)
    if modified_files==[]:
        print("[+] 由于未知错误无法比较两个提交")
        # 删除克隆的仓库
        delete_path(repo_path)

        # 删除git文件夹
        print("[！！]删除git文件夹[！！]")
        delete_path(folder_path)

        
        tittle = item.get("tittle")
        status = item.get("status")
        type = item.get("type")
        module = item.get("project")
        target = item.get("target")
        folder_name = item.get("link").split('/')[-1]

        commit_dist = item.get("commit_dist")
        module_name, compare_url = next(iter(commit_dist.items()))
        commit_url = compare_url.split('...')[0].replace("compare","commit")
        commit_url_new = commit_url.split("/commit/")[0]+"/commit/"+compare_url.split('...')[-1]
        log_file = os.path.join(base_dir, f"{folder_name}.log")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"tittle:{tittle}\nstatus:{status}\ntype:{type}\ncommit_url:{commit_url}\ncommit_url_new:{commit_url_new}\nmodule:{module}\ntarget:{target}\n")
            f.write("unknown error, cannot compare!")
            f.write("\n" + "=" * 50 + "\n")
        return []

    if not modified_files:
        print("[-] 没有找到修改的文件")
        return

    print(f"[+] 发现 {len(modified_files)} 个修改文件")

    with open(file_path, "w") as f:
        for a, b in zip(modified_files, modified_files):
            f.write(f"{a},{b}\n")
    
    print("[+] 记录所有文件到txt中")

    # 下载并保存旧版本的文件
    if save_old_version_files(repo_path, modified_files, output_dir, old_commit):
        print("[+] 所有旧版本的修改文件已保存")
        # 删除克隆的仓库
        delete_path(repo_path)
    else:
        print("[+] 存在新文件加入")
        # 删除克隆的仓库
        delete_path(repo_path)

        # 删除git文件夹
        print("[！！]删除git文件夹[！！]")
        delete_path(folder_path)

        
        tittle = item.get("tittle")
        status = item.get("status")
        type = item.get("type")
        module = item.get("project")
        target = item.get("target")
        folder_name = item.get("link").split('/')[-1]

        commit_dist = item.get("commit_dist")
        module_name, compare_url = next(iter(commit_dist.items()))
        commit_url = compare_url.split('...')[0].replace("compare","commit")
        commit_url_new = commit_url.split("/commit/")[0]+"/commit/"+compare_url.split('...')[-1]
        log_file = os.path.join(base_dir, f"{folder_name}.log")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"tittle:{tittle}\nstatus:{status}\ntype:{type}\ncommit_url:{commit_url}\ncommit_url_new:{commit_url_new}\nmodule:{module}\ntarget:{target}\n")
            f.write("new files join in!")
            f.write("\n" + "=" * 50 + "\n")
        return []

    return modified_files






import subprocess
import argparse
import shutil
import os
import os
import re
import difflib



def normalize_dockerfile(filepath1, filepath2):
    with open(filepath1, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    normalized_lines = []
    buffer = ""

    for line in lines:
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buffer += stripped[:-1].rstrip() + " "  # 去掉斜杠，末尾补空格
        else:
            buffer += stripped
            # 处理完整的一行
            normalized_lines.append(buffer.strip())
            buffer = ""

    # 如果最后还有残留
    if buffer:
        normalized_lines.append(buffer.strip())

    # === 处理 git clone 后有 && 的情况 ===
    final_lines = []
    for line in normalized_lines:
        if "git clone" in line and "&&" in line:
            # 只对包含git clone且有&&的行处理
            parts = line.split("&&",1)
            git_clone_part = parts[0].strip()
            other_commands = parts[1].strip()
            final_lines.append(git_clone_part + "\n")
            final_lines.append("RUN " + other_commands + "\n")
        else:
            final_lines.append(line + "\n")

    with open(filepath2, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)

    print("Dockerfile规范化完成！")

def extract_git_clone(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    project_names = []
    clone_paths = []
    line_numbers = []

    for idx, line in enumerate(lines):
        if "git clone" not in line:
            continue

        # 先按 &&
        subcommands = line.split("&&")
        for subcmd in subcommands:
            if "git clone" not in subcmd:
                continue

            subcmd = subcmd.strip()

            # 空格切开
            parts = subcmd.split()

            if len(parts) < 3:
                continue  # 不够元素，跳过

            # 最后一个块
            last_part = parts[-1]

            if last_part.startswith("https://github.com/") or last_part.startswith("https://code.videolan.org/"):
                repo_name = last_part.rstrip("/").split("/")[-1]
                if repo_name.endswith(".git"):
                    repo_name = repo_name[:-4]
                project_names.append(repo_name)
                clone_paths.append("")  # 无路径
            else:
                # last_part是路径
                clone_paths.append(last_part)
                # 仓库名字来源于url
                url = parts[-2]
                if url.startswith("https://github.com/") or url.startswith("https://code.videolan.org/"):
                    repo_name = url.rstrip("/").split("/")[-1]
                    if repo_name.endswith(".git"):
                        repo_name = repo_name[:-4]
                    project_names.append(repo_name)
                else:
                    project_names.append("")  # 不标准情况

            line_numbers.append(idx)

    return project_names, clone_paths, line_numbers

def modify_dockerfile(target_module_name, commit_hash):

    
    dockerfile_path = f"projects/{target_module_name}/Dockerfile"
    backup_path = f"projects/{target_module_name}/Dockerfile.bak"
    
    # 备份 Dockerfile
    if not os.path.exists(backup_path):
        os.rename(dockerfile_path, backup_path)
    
    normalize_dockerfile(backup_path,dockerfile_path)
    project_names, clone_paths, line_numbers = extract_git_clone(dockerfile_path)
    print(project_names)
    print(clone_paths)
    print(line_numbers)

    # 第二步：寻找最佳匹配
    best_idx = -1
    best_ratio = 0

    for i, proj in enumerate(project_names):
        seq_matcher = difflib.SequenceMatcher(None, target_module_name, proj)
        ratio = seq_matcher.ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = i

    if best_idx == -1 or best_ratio < 0.05:
        print("未找到合适的模块匹配！")
        return

    print(f"找到匹配项目: {project_names[best_idx]} (匹配度 {best_ratio*100:.2f}%)")

    real_module = clone_paths[best_idx] if clone_paths[best_idx] else project_names[best_idx]

    # 第三步：准备插入内容
    new_lines = [
        f"RUN cd {real_module} && \\\n",
        f"  if [ \"$(git rev-parse --is-shallow-repository)\" = \"true\" ]; then git fetch --unshallow; fi && \\\n",
        f"  git fetch && git checkout {commit_hash}\n"
    ]

    # 第四步：读取原文件
    with open(dockerfile_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 插入到目标行+1的位置
    insert_idx = line_numbers[best_idx] + 1
    lines = lines[:insert_idx] + new_lines + lines[insert_idx:]

    # 第五步：写回
    with open(dockerfile_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("成功插入指定的git checkout命令！")

    print("修改完成！")

    return real_module


def write_lists_to_file(file_path, list1, list2):
    """将两个等长列表写入文件"""
    with open(file_path, "w") as f:
        for a, b in zip(list1, list2):
            f.write(f"{a},{b}\n")

def read_lists_from_file(file_path):
    """从文件读取两个列表"""
    list1, list2 = [], []
    with open(file_path, "r") as f:
        for line in f:
            a, b = line.strip().split(",")  # 解析每行数据
            list1.append(a)
            list2.append(b)
    return list1, list2


def run_command(cmd, cwd=None, interactive=False):
    """运行 shell 命令"""
    if interactive:
        result = subprocess.run(cmd, shell=True, cwd=cwd)
    else:
        result = subprocess.run(cmd, shell=True, cwd=cwd, text=True, capture_output=True)
        if result.returncode != 0:
            print(f"Error running command: {cmd}\n{result.stderr}")
            return f"error running command: {cmd}\n{result.stdout + result.stderr}" 
        return result.stdout.strip()
        # return result.stdout + result.stderr


def run_command_with_fallback(cmd1, cmd2, cwd=None, interactive=False):
    """先运行 cmd1，如果失败则运行 cmd2"""
    if interactive:
        result = subprocess.run(cmd1, shell=True, cwd=cwd)
        if result.returncode == 0:
            return
        print(f"First command failed: {cmd1}")
        subprocess.run(cmd2, shell=True, cwd=cwd)
    else:
        result = subprocess.run(cmd1, shell=True, cwd=cwd, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout + result.stderr
        print(f"First command failed: {cmd1}\n{result.stderr}")

        fallback_result = subprocess.run(cmd2, shell=True, cwd=cwd, text=True, capture_output=True)
        if fallback_result.returncode != 0:
            print(f"Fallback command also failed: {cmd2}\n{fallback_result.stderr}")
        return fallback_result.stdout + fallback_result.stderr


    
# def build_img(module, commit_hash, src_file):
def build_img(item,depth):
    folder_name = item.get("link").split('/')[-1]
    folder_path = os.path.join(base_dir, folder_name)
    module = item.get("project")
    sanitizer = item.get("sanitizer").split(' ')[0]
    commit_dist = item.get("commit_dist")
    module_name, compare_url = next(iter(commit_dist.items()))
    # if compare_url=="null": return "fail"
    if not compare_url.startswith("https://github.com/"): return "fail"
    commit_url = compare_url.split('...')[0].replace("compare","commit")
    # commit_hash = commit_url.split("/commit/")[-1]

    # commit_hash_2 = get_previous_commits(commit_url, depth, token)[-1]
    # # 88报错没有构建fuzzer
    # # 87不报错
    # # 91有cmake文件
    # # 92没有
    # commit_hash = commit_hash_2

    if depth ==0:
        commit_hash = compare_url.split('...')[-1]
        if "/compare/" not in compare_url: commit_hash = commit_url.split("/commit/")[-1]

    elif depth == 1:
        commit_hash = commit_url.split("/commit/")[-1]
    
    elif depth >1:
        commit_hash_2 = get_previous_commits(commit_url, depth, token)[-1]
        # 88报错没有构建fuzzer
        # 87不报错
        # 91有cmake文件
        # 92没有
        commit_hash = commit_hash_2
    
    # commit_hash = compare_url.split('...')[-1]

    # src_file = os.path.join(folder_path, "testcase")
    src_file = f"testcase_{folder_name}"
    print(f"[+] 修改 {module} dockerfile 获取指定版本{commit_hash}")
    real_module = modify_dockerfile(module, commit_hash)
    
    print(f"[+] 重新构建 image; depth:{depth}")
    run_command(f"python infra/helper.py pull_images")
    output = run_command(f"yes | python infra/helper.py build_image {module}")

    print(f"[+] 进入容器 {module} 并检查 Git 操作")

    # 直接用 docker exec 运行命令，避免 `infra/helper.py shell` 进入交互式 shell
    container_name = f"oss-fuzz-{module}"
    # run_command(f"docker run --rm -it gcr.io/oss-fuzz/{module} git rev-parse HEAD", interactive=True)
    # run_command(f"docker run --rm -it gcr.io/oss-fuzz/{module} bash -c 'cd /src/{module} && git rev-parse HEAD'", interactive=True)

    # run_command_with_fallback(f"docker run --rm -it gcr.io/oss-fuzz/{module} git rev-parse HEAD",f"docker run --rm -it gcr.io/oss-fuzz/{module} bash -c 'cd /src/{module} && git rev-parse HEAD'", interactive=True)

    real_module_dir = real_module.split("/")[-1]
    check_commit =  run_command(f"docker run --rm -it gcr.io/oss-fuzz/{module} bash -c 'cd /src/{real_module_dir} && git rev-parse HEAD'")
    print(f"check_commit:{check_commit}\ncommit_hash:{commit_hash}")

    print("[+] 重新编译 fuzzer")
    run_command_with_fallback(f"python infra/helper.py build_fuzzers --sanitizer {sanitizer} --architecture x86_64 {module}",f"python infra/helper.py build_fuzzers --sanitizer {sanitizer} --architecture i386 {module}")
    # run_command(f"python infra/helper.py build_fuzzers {module}")

    # run_command_with_fallback(f"python infra/helper.py build_fuzzers --clean {module}",f"python infra/helper.py build_fuzzers {module}")

    # try:
    #     run_command(f"python infra/helper.py build_fuzzers --clean {module}")
    #     # run_command(f"python infra/helper.py build_fuzzers {module}")
    # except:
    #     print(f"[+] 重新编译 fuzzer 失败")
    #     run_command(f"python infra/helper.py build_fuzzers {module}")

    print(f"[+] 在容器 {module} 中创建 testcase 文件夹")
    run_command(f"docker run --rm -it gcr.io/oss-fuzz/{module} rm -rf /out/testcase", interactive=True)
    run_command(f"docker run --rm -it gcr.io/oss-fuzz/{module} mkdir -p /out/testcase", interactive=True)

    print("[+] 复制测试文件到容器主机路径")
    dst_dir = f"build/out/{module}/testcase"
    # src_dir = f"testcase/{src_file}"
    src_dir = os.path.join(folder_path, src_file)
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy(src_dir, dst_dir)
    print(f"文件 {src_dir} 已复制到 {dst_dir}")
    # if "rror running command:" in output:
    if commit_hash != check_commit:
        return "question"
    return "success"


# python infra/helper.py build_fuzzers libultrahdr
# python infra/helper.py shell libultrahdr
# python infra/helper.py reproduce libultrahdr ultrahdr_dec_fuzzer build/out/libultrahdr/testcase/testcase_370032374


def test_poc(item, change_files,depth):
    tittle = item.get("tittle")
    status = item.get("status")
    type = item.get("type")
    module = item.get("project")
    target = item.get("target")
    folder_name = item.get("link").split('/')[-1]

    commit_dist = item.get("commit_dist")
    module_name, compare_url = next(iter(commit_dist.items()))
    commit_url = compare_url.split('...')[0].replace("compare","commit")
    commit_url_new = commit_url.split("/commit/")[0]+"/commit/"+compare_url.split('...')[-1]
    
    print("[$] 复现testcase")
    output = run_command(f"python infra/helper.py reproduce {module} {target} build/out/{module}/testcase/testcase_{folder_name}")
    crash_keywords = ["error", "ERROR", "Segmentation fault", "AddressSanitizer", "FATAL"]
    crash_detected = any(keyword in output for keyword in crash_keywords)

    # 记录到日志文件
    if not crash_detected:
        log_file = os.path.join(base_dir, f"{folder_name}_dep:{depth}.log")
    else:
        log_file = os.path.join(base_dir, f"{folder_name}_{len(change_files)}_dep:{depth}.log")

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"tittle:{tittle}\nstatus:{status}\ntype:{type}\ncommit_url:{commit_url}\ncommit_url_new:{commit_url_new}\nmodule:{module}\ntarget:{target}\n")
        f.write(f"have {len(change_files)} changed files:{change_files}")
        f.write("\n" + "=" * 50 + "\n")
        f.write(output)
        f.write("\n" + "=" * 50 + "\n")
        f.write("PoC Triggered: {}\n".format("YES" if crash_detected else "NO"))

    print(f"Execution completed. Log saved in {log_file}. PoC Triggered: {'YES' if crash_detected else 'NO'}")
    if not crash_detected:
        print("[！！]删除镜像[！！]")
        run_command(f"docker rmi -f gcr.io/oss-fuzz/{module}")
        # final_end(item)
        return "fail"
    else:
        if len(change_files) > 3:
            print("[！！]删除镜像[！！]")
            run_command(f"docker rmi -f gcr.io/oss-fuzz/{module}")
            # final_end(item)
            return "fail"
        else:
            print("[！！]删除镜像[！！]")
            run_command(f"docker rmi -f gcr.io/oss-fuzz/{module}")
            # final_end(item)
            return "success"

def final_end(item):
    folder_name = item.get("link").split('/')[-1]
    folder_path = os.path.join(base_dir, folder_name)

    # 删除git文件夹
    print("[！！]删除git文件夹[！！]")
    delete_path(folder_path)
    # 删除镜像
    # docker system prune -a --volumes -f
    # print("[！！]删除镜像[！！]")
    # run_command(f"docker system prune -a --volumes -f")
    # run_command(f"docker rmi -f gcr.io/oss-fuzz/{module}")
    # 删除build文件夹
    print("[！！]删除build文件夹[！！]")
    module = item.get("project")
    delete_path_sudo_cmd(f"build/out/{module}")
    delete_path_sudo_cmd(f"build/work/{module}")

# 80 42538160

with open("[].txt", 'r', encoding='utf-8') as f:
    twice_filenames = [line.strip() for line in f]
print(twice_filenames)

for i in range(len(data)):
    
    # if data[i].get("link").split('/')[-1] in twice_filenames:
    #     continue
    # if not data[i].get("link").split('/')[-1]=="42537389":
    #     continue
    # if not data[i].get("link").split('/')[-1]=="42537728":
    #     continue
    # if not data[i].get("link").split('/')[-1]=="370032374":
    #     continue
    # if not data[i].get("link").split('/')[-1]=="369652657":
    #     continue
    # if not data[i].get("link").split('/')[-1]=="369216702":
    #     continue
    if data[i].get("project")=="gdal" or data[i].get("project")=="trafficserver":
        continue


    # if i>8:
    if i<=421:
    # if i<=329:
    # if i<=198:
    # if i<=174:
    # if i<=142:
    # if i<=75:
    # if i<=45:
    # if i<=13:
        continue
    # if i!=7:
    #     continue
    # if i>10:
    #     break
    # if i>3:
    #     break
    if len(data[i]["commit_dist"])>1:
        print(f"---------{i}----------")
        continue
    # create_folder_and_download(data[i])
    # # change_files = get_diff(data[i])
    # # if change_files == []:
    # #     print(f"---------{i}----------")
    # #     continue
    # change_files=["jump get_diff!"]
    # build_img(data[i],depth)
    # poc_result = test_poc(data[i], change_files)
    # print(f"---------{i}----------")
    # if poc_result=="success":
    #     break
    # # final_end(data[i])
    depth = 1
    create_folder_and_download(data[i])

    # depth = 0
    # change_files=["jump get_diff!"]
    # build_img(data[i],depth)
    # poc_result = test_poc(data[i], change_files,depth)
    # final_end(data[i])

    while True:
        change_files=["jump get_diff!"]
        img_result = build_img(data[i],depth)
        if img_result == "fail":
            break
        elif img_result == "question":
            change_files=["img_error","img_error","img_error"]
        poc_result = test_poc(data[i], change_files,depth)
        print(f"---------{i}----------")
        depth=depth*2
        if poc_result=="success":
            final_end(data[i])
            break
        if depth>=1024:
            final_end(data[i])
            break
    