from pyhive import hive
from queue import Queue
import threading
from django.conf import settings


class HiveConnectionPoolManager:
    """Hive 多数据源连接池管理（无认证）"""

    _instance_lock = threading.Lock()
    _pools = {}  # 存储不同数据源的连接池

    def __init__(self, max_connections=10):
        self.max_connections = max_connections

    @classmethod
    def instance(cls, max_connections=10):
        """获取单例实例"""
        if not hasattr(cls, "_instance"):
            with cls._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = cls(max_connections)
        return cls._instance

    def get_pool(self, db_name):
        """
        获取指定 Hive 数据源的连接池
        :param db_name: Hive 数据库名称（在 settings.HIVE_DATABASES 里定义）
        """
        if db_name not in settings.HIVE_DATABASES:
            raise ValueError(f"未找到 Hive 数据库配置: {db_name}")

        db_config = settings.HIVE_DATABASES[db_name]
        key = f"{db_config['HOST']}:{db_config['PORT']}:{db_config['DATABASE']}"

        with self._instance_lock:
            if key not in self._pools:
                self._pools[key] = self._create_pool(
                    db_config["HOST"], db_config["PORT"], db_config["DATABASE"], db_config["AUTH"]
                )
        return self._pools[key]

    def _create_pool(self, host, port, database, auth):
        """创建新的连接池（无认证）"""
        pool = Queue(self.max_connections)
        for _ in range(self.max_connections):
            conn = self._create_connection(host, port, database, auth)
            pool.put(conn)
        return pool

    def _create_connection(self, host, port, database, auth):
        """创建新的 Hive 连接（无认证）"""
        return hive.Connection(
            host=host,
            port=port,
            database=database,
            auth=auth if auth != "NONE" else None  # 如果 AUTH=NONE，则不传递认证参数
        )

    def get_connection(self, db_name):
        """获取指定 Hive 数据库的连接"""
        # pool = self.get_pool(db_name)
        # if pool.empty():
        db_config = settings.HIVE_DATABASES[db_name]
        return self._create_connection(
                db_config["HOST"], db_config["PORT"], db_config["DATABASE"], db_config["AUTH"]
            )
        # return pool.get()

    def release_connection(self, conn, db_name):
        """释放连接，归还到连接池"""
        db_config = settings.HIVE_DATABASES[db_name]
        key = f"{db_config['HOST']}:{db_config['PORT']}:{db_config['DATABASE']}"

        with self._instance_lock:
            if key in self._pools and not self._pools[key].full():
                self._pools[key].put(conn)
            else:
                try:
                    conn.close()
                except Exception as e:
                    pass

    def remove_connection(self, conn, db_name):
        """从连接池中移除失效的连接，并重新创建一个新的连接放回池子"""
        db_config = settings.HIVE_DATABASES[db_name]
        key = f"{db_config['HOST']}:{db_config['PORT']}:{db_config['DATABASE']}"

        with self._instance_lock:
            if key in self._pools:
                pool = self._pools[key]

                # **从池子里删除当前失效的 conn**
                temp_connections = []
                while not pool.empty():
                    temp_conn = pool.get()
                    if temp_conn == conn:
                        # **发现失效的连接，关闭它**
                        try:
                            conn.close()
                            print(f"已移除失效连接: {conn}")
                        except Exception as e:
                            print(f"关闭失效连接失败: {e}")
                    else:
                        # **保存仍然可用的连接**
                        temp_connections.append(temp_conn)

                # **把所有可用的连接重新放回池子**
                for c in temp_connections:
                    pool.put(c)

                # **创建一个新连接，并放回池子**
                new_conn = self._create_connection(
                    db_config["HOST"], db_config["PORT"], db_config["DATABASE"], db_config["AUTH"]
                )
                pool.put(new_conn)  # 放回新连接
                print(f"已创建新连接并加入池子: {new_conn}")
