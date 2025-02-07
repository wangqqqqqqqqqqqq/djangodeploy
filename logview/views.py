import json
import urllib.request

from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import HiveQuery
def get_latest_date():
    """获取今天的日期作为查询起点"""
    return datetime.today().strftime('%Y-%m-%d')


def generate_pagination_context(page):
    """
    生成分页信息:
    - 默认显示 `1 - 10`
    - `<<` 跳转到上一组
    - `>>` 跳转到下一组
    """
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
def app_info_view(request):
    """渲染 `app_info` 页面"""
    db_name = "hive3"
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    hive_query = HiveQuery(db_name)
    data = hive_query.get_app_info(page, page_size)

    pagination = generate_pagination_context(page)

    return render(request, "capture/app_info.html", {"data": data, "page": page, "page_size": page_size, "pagination": pagination})

@login_required
def ip_info_view(request):
    """渲染 `ip_info` 页面"""
    db_name = "hive3"
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    hive_query = HiveQuery(db_name)
    data = hive_query.get_ip_info(page, page_size)

    pagination = generate_pagination_context(page)

    return render(request, "capture/ip_info.html", {"data": data, "page": page, "page_size": page_size, "pagination": pagination})

@login_required
def stream_log_cloudip(request):
    db_name = "hive3"
    if  request.POST.get("date"):
        now_date=request.POST.get("date")
        cloud_ip=request.POST.get("cloud_ip")
        page=int(request.POST.get("page",1))
        page_size=int(request.POST.get("page_size",10))
        hive_query=HiveQuery(db_name)
        data=hive_query.get_network_logs_by_cloudip(cloudip=cloud_ip,date=now_date,page=page,page_size=page_size)
        pagination=generate_pagination_context(page)
        return render(request,"capture/stream_log_cloudip.html",
                      {"data":data,"page":page,"page_size":page_size,
                       "pagination":pagination,"cloudip":cloud_ip,"date":now_date})
    else:
        cloud_ip=request.GET.get("cloud_ip")
        page=int(request.GET.get("page",1))
        page_size = int(request.POST.get("page_size", 10))
        if request.GET.get("date"):
            now_date=request.GET.get("date")
        else:
            now_date=get_latest_date()
        hive_query=HiveQuery(db_name)
        data=hive_query.get_network_logs_by_cloudip(cloudip=cloud_ip,date=now_date,page=page,page_size=page_size)
        pagination=generate_pagination_context(page)
        return render(request,"capture/stream_log_cloudip.html",
                      {"data":data,"page":page,"page_size":page_size,
                       "pagination":pagination,"cloudip":cloud_ip,"date":now_date})
@login_required
def cloud_log(request):
    db_name = "hive2"
    hive_query=HiveQuery(db_name)
    data=hive_query.get_cloud_ip()
    print(data)
    return render(request,"capture/cloud_ip.html",{"data":data})
@login_required
def stream_log_ip(request):
    db_name="hive3"
    if request.POST.get("date"):
        now_date=request.POST.get("date")
        ip=request.POST.get("ip")
        page = int(request.POST.get("page", 1))
        page_size = int(request.POST.get("page_size", 10))
        hives=HiveQuery(db_name)
        data=hives.get_network_logs_by_ip(ip,now_date,page,page_size)
        pagination=generate_pagination_context(page)
        return render(request,"capture/stream_log_ip.html",
                      {"data":data,"page":page,"page_size":page_size,
                       "pagination":pagination,"ip":ip,"date":now_date})
    else:
        if request.GET.get("date"):
            now_date = request.GET.get("date")
        else:
            now_date = get_latest_date()
        ip = request.GET.get("ip")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))
        hives=HiveQuery(db_name)
        data = hives.get_network_logs_by_ip(ip, now_date, page, page_size)
        pagination = generate_pagination_context(page)
        return render(request, "capture/stream_log_ip.html",
                      {"data": data, "page": page, "page_size": page_size,
                       "pagination": pagination,"ip":ip,"date":now_date})
@login_required
def http_log_ip(request):
    db_name = "hive2"
    if request.POST.get("date"):
        now_date = request.POST.get("date")
        ip=request.POST.get("ip")
        page = int(request.POST.get("page", 1))
        page_size = int(request.POST.get("page_size", 10))
        hives = HiveQuery(db_name)
        data = hives.get_http_logs(ip, now_date, page, page_size)
        pagination=generate_pagination_context(page)
        return render(request,"capture/stream_http_log.html",{"data": data, "page": page, "page_size": page_size,
                       "pagination": pagination,"ip":ip,"date":now_date})
    else:
        if request.GET.get("date"):
            now_date = request.GET.get("date")
        else:
            now_date = get_latest_date()
        ip = request.GET.get("ip")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))
        hives = HiveQuery(db_name)
        data = hives.get_http_logs(ip, now_date, page, page_size)
        pagination = generate_pagination_context(page)
        return render(request, "capture/stream_http_log.html", {"data": data, "page": page, "page_size": page_size,
                                                                "pagination": pagination,"ip":ip,"date":now_date})

def fetch_geolocation(ip):
    """调用 IP-API 获取地理信息（同步方式）"""
    url = f"http://ip-api.com/json/{ip}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            geo_data = json.loads(response.read().decode())
            if geo_data.get("status") == "success":
                return {
                    "country": geo_data.get("country"),
                    "region": geo_data.get("regionName"),
                    "city": geo_data.get("city"),
                    "lat": geo_data.get("lat"),
                    "lon": geo_data.get("lon"),
                    "isp": geo_data.get("isp"),
                }
    except Exception as e:
        print(f"Error fetching geolocation for {ip}: {e}")
    return {
        "country": "UNKNOWN",
        "region": "UNKNOWN",
        "city": "UNKNOWN",
        "lat": 0.0,
        "lon": 0.0,
        "isp": "UNKNOWN"
    }
@login_required
def http_details(request, ip):
    """查询 `ip_info` 详情，若数据不完整则补充地理信息"""
    db_name = "hive3"
    hives = HiveQuery(db_name)
    details = hives.get_ip_details(ip)

    if not details:  # 如果 details 为空
        return JsonResponse({"error": "No data found"}, status=404)

    ip_info = details[0]  # 取第一条记录

    # 如果 `country` 为 "UNKNOWN"，则调用 `fetch_geolocation()` 补充数据
    if ip_info.get("country") == "UNKNOWN":
        geo_data = fetch_geolocation(ip)
        ip_info.update(geo_data)  # 更新缺失的数据

    return JsonResponse(ip_info)  # 返回完整的 IP 详情

