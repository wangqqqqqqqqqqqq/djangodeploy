from django.db import models

# Create your models here.
from talktive.hive_client import HiveConnectionPoolManager

class HiveQuery:
    """封装 Hive 数据库的查询"""

    def __init__(self, db_name):
        """选择 Hive 数据源（如 hive2 或 hive3）"""
        self.db_name = db_name
        self.pool_manager = HiveConnectionPoolManager.instance()

    def execute_query(self, sql, retry_attempts=50):
        """执行 SQL 查询，遇到 read timeout 重新创建连接并重试"""
        conn = None
        cursor = None
        attempt = 0

        while attempt < retry_attempts:
            try:
                conn = self.pool_manager.get_connection(self.db_name)
                cursor = conn.cursor()
                cursor.execute(sql)

                columns = [desc[0] for desc in cursor.description]  # 获取列名
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]  # 返回 [{列名: 值}]

            except Exception as e:
                error_msg = str(e).lower()
                print(f"执行 SQL 失败 (尝试 {attempt + 1}/{retry_attempts})，错误: {error_msg}")
                self.pool_manager.remove_connection(conn, self.db_name)
                attempt += 1  # 记录重试次数
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        return {"error": "查询超时，重试失败"}
    def get_app_info(self, page=1, page_size=10):
        """查询 `app_info` 表（分页）"""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT app_id, app_name, app_category
        FROM app_info
        LIMIT {page_size} OFFSET {offset}
        """
        return self.execute_query(sql)
    def get_ip_info(self, page=1, page_size=10):
        """查询 `ip_info` 表（分页）"""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT ip, region, country, city, lat, lon, isp
        FROM ip_info
        LIMIT {page_size} OFFSET {offset}
        """
        return self.execute_query(sql)
    def get_ip_details(self,ip):
        sql=f"""
            SELECT ip, region, country, city, lat, lon, isp
            FROM ip_info where ip='{ip}'
        """
        return self.execute_query(sql)

    def get_network_logs(self, page=1, page_size=10):
        """查询 `network_logs` 表（分页）"""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT `timestamp`, source_ip, destination_ip, source_port, destination_port,
               protocol, ip_version, cloud_ip, predicted_label, log_date
        FROM network_logs
        LIMIT {page_size} OFFSET {offset}
        """
        return self.execute_query(sql)

    def get_http_logs(self, ip,timestamp,page=1, page_size=10):
        """查询 `http_logs` 表（分页）"""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT `timestamp`, host_ip, source_ip, destination_ip, source_port, destination_port,
               protocol, cloudip, fwd_header_length, packet_length, http_payload, predicted_label, log_date
        FROM http_logs where host_ip='{ip}' and log_date='${timestamp}'
        LIMIT {page_size} OFFSET {offset}
        """
        return self.execute_query(sql)

    def get_cloud_ip(self):
        """查询 `cloud_ip_info` 表（不分页）"""
        sql = "SELECT cloudip FROM cloud_ip_info"
        return self.execute_query(sql)

    def get_all_ip(self, page=1, page_size=10):
        """查询 `source_ip_info` 表（分页）"""
        offset = (page - 1) * page_size
        sql = f"SELECT source_ip, destination_ip FROM source_ip_info LIMIT {page_size} OFFSET {offset}"
        return self.execute_query(sql)

    def get_network_logs_by_cloudip(self, cloudip, date, page=1, page_size=10):
        """按 `cloud_ip` 过滤 `network_logs` 表，按 `log_date` 查询"""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT `timestamp`, source_ip, destination_ip, source_port, destination_port,
               protocol, ip_version, cloud_ip, predicted_label, log_date
        FROM network_logs
        WHERE cloud_ip = '{cloudip}' AND log_date = '{date}'
        LIMIT {page_size} OFFSET {offset}
        """
        return self.execute_query(sql)

    def get_network_logs_by_ip(self, ip, date, page=1, page_size=10):
        """按 `source_ip` 过滤 `network_logs` 表"""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT `timestamp`, source_ip, destination_ip, source_port, destination_port,
               protocol, ip_version, cloud_ip, predicted_label, log_date
        FROM network_logs
        WHERE source_ip = '{ip}' AND log_date = '{date}'
        LIMIT {page_size} OFFSET {offset}
        """
        return self.execute_query(sql)

    def get_cloud_ip(self, page=1, page_size=10):
        """查询 `cloud_info` 表（分页）"""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT cloudip FROM cloud_info 
        LIMIT {page_size} OFFSET {offset}
        """
        return self.execute_query(sql)

    def get_process_info(self, page=1, page_size=10):
        """查询 `process_info` 表（分页）"""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT pid, process_name, cloudip FROM process_info 
        LIMIT {page_size} OFFSET {offset}
        """
        return self.execute_query(sql)

    def get_syscall_logs(self, page=1, page_size=10):
        """查询 `syscall_logs` 表（分页）"""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT pid, `timestamp`, syscall, predicted_result FROM syscall_logs 
        LIMIT {page_size} OFFSET {offset}
        """
        return self.execute_query(sql)