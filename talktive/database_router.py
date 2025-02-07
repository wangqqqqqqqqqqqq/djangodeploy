class MultiDBRouter:
    """
    自定义数据库路由
    """

    def db_for_read(self, model, **hints):
        """查询时使用 Hive"""
        if hasattr(model, "_use_hive_db"):
            return "hive"
        return "default"

    def db_for_write(self, model, **hints):
        """Hive 仅允许查询，不允许写入"""
        if hasattr(model, "_use_hive_db"):
            return None  # 禁止写入
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """不允许跨数据库关联"""
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """默认数据库允许迁移，Hive 不迁移"""
        return db == "default"
