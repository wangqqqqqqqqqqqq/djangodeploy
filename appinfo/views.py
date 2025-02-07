from django.contrib.auth.decorators import login_required
from django.shortcuts import render
# from .models import *
# Create your views here.
import re
from .models import *
def convert_syscall_numbers_to_names(syscall_sequence):
    """将 syscall 号码列表转换为对应的 syscall 名称"""
    syscall_nums = syscall_sequence.split(", ")  # 拆分字符串
    syscall_names = [mapping_syscall.get(int(num), f"UNKNOWN({num})") for num in syscall_nums[:30]]  # 获取前 30 个
    return ", ".join(syscall_names)  # 转换为字符串返回
def parse_adfa_ld_file(file_path):
    """
    解析 ADFA-LD 的 syscall 列表文件，并提取 syscall 定义。
    :param file_path: 包含 ADFA-LD syscall 定义的文件路径
    :return: 一个字典，key 是 syscall 名称，value 是对应的序号
    """
    syscall_mapping = {}
    mapping_syscall = {}
    # 打开并读取文件内容
    with open(file_path, "r") as file:
        lines = file.readlines()

    # 匹配 `#define __NR_` 和 `__SYSCALL` 的正则表达式
    define_pattern = re.compile(r"#define\s+(__NR_\w+)\s+(\d+)")
    syscall_pattern = re.compile(r"__SYSCALL\s*\(\s*(\S+)\s*,\s*(\w+)\s*\)")

    # 遍历文件行，查找匹配
    for line in lines:
        define_match = define_pattern.match(line)
        syscall_match = syscall_pattern.match(line)

        # 如果匹配到 `#define` 定义
        if define_match:
            syscall_name = define_match.group(1)  # `__NR_xxx`
            syscall_num = int(define_match.group(2))  # syscall 序号
            syscall_mapping[syscall_name] = syscall_num
            mapping_syscall[syscall_num]=syscall_name
        # 如果匹配到 `__SYSCALL` 定义
        elif syscall_match:
            syscall_nr = syscall_match.group(1)  # `__NR_xxx`
            syscall_func = syscall_match.group(2)  # `sys_xxx`
            # 创建 syscall -> label 映射
            if syscall_nr in syscall_mapping:
                syscall_mapping[syscall_func] = syscall_mapping[syscall_nr]
                mapping_syscall[syscall_mapping[syscall_nr]]=syscall_func

    return syscall_mapping,mapping_syscall
syscall_mapping,mapping_syscall=parse_adfa_ld_file("ADFA-LD+Syscall+List.txt")
def generate_pagination_context(page):
    """生成分页信息（默认显示 1-10 页）"""
    page_group_size = 10  # 每组最多 10 页
    current_group = (page - 1) // page_group_size  # 计算当前页所在的组
    start_page = current_group * page_group_size + 1
    end_page = start_page + page_group_size - 1
    pages = list(range(start_page, end_page + 1))

    return {
        "pages": pages,
        "prev_group": max(1, start_page - page_group_size),
        "next_group": start_page + page_group_size
    }


@login_required
def get_syscall_logs(request):
    """渲染 `syscall_logs` 页面"""
    db_name = "hive1"
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    hive_query = HiveQuery(db_name)
    data = hive_query.get_syscall_logs(page, page_size)

    # 处理 syscall 字段，转换编号为 syscall 名称
    for row in data:
        row["syscall"] = convert_syscall_numbers_to_names(row["syscall"])

    pagination = generate_pagination_context(page)

    return render(request, "applog/syscall_logs.html", {
        "data": data,
        "page": page,
        "page_size": page_size,
        "pagination": pagination
    })
@login_required
def get_process_info(request):
    """渲染 `process_info` 页面"""
    db_name = "hive1"
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    hive_query = HiveQuery(db_name)
    data = hive_query.get_process_info(page, page_size)

    pagination = generate_pagination_context(page)

    return render(request, "applog/process_info.html", {"data": data, "page": page, "page_size": page_size, "pagination": pagination})


@login_required
def get_cloud_ip(request):
    """渲染 `cloud_info` 页面"""
    db_name = "hive1"
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    hive_query = HiveQuery(db_name)
    data = hive_query.get_cloud_ip(page, page_size)

    pagination = generate_pagination_context(page)

    return render(request, "applog/cloud_ip.html", {"data": data, "page": page, "page_size": page_size, "pagination": pagination})