# 导入操作系统相关模块，用于文件路径和文件存在性检查
import os
# 导入正则表达式模块，用于处理别名匹配
import re

# 导入项目中的常量定义
import utils.constants as constants
# 从工具模块中导入路径处理和名称格式化函数
from utils.tools import get_real_path, resource_path, format_name


# 定义一个别名处理类 Alias
class Alias:
    def __init__(self):
        # 主名称到别名集合的映射字典
        self.primary_to_aliases: dict[str, set[str]] = {}
        # 别名到主名称的映射字典
        self.alias_to_primary: dict[str, str] = {}
        # 正则表达式模式到主名称的映射列表（用于正则匹配）
        self.pattern_to_primary: list[tuple[re.Pattern, str]] = []

        # 获取别名配置文件路径
        real_path = get_real_path(resource_path(constants.alias_path))
        # 如果文件存在，则读取内容
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                for line in f:
                    # 忽略空行、注释行和不包含逗号的行
                    if line.strip() and not line.startswith("#") and "," in line:
                        # 按逗号分割并去除空格
                        parts = [p.strip() for p in line.split(",")]
                        # 第一项为主名称
                        primary = parts[0]
                        # 后续项为别名集合
                        aliases = set(parts[1:])
                        # 将格式化后的主名称也加入别名集合
                        aliases.add(format_name(primary))
                        # 保存主名称到别名集合的映射
                        self.primary_to_aliases[primary] = aliases
                        # 遍历别名集合，建立别名到主名称的映射
                        for alias in aliases:
                            self.alias_to_primary[alias] = primary

                            # ✅ 如果别名以 re: 开头，则视为正则表达式
                            if alias.startswith("re:"):
                                raw_pattern = alias[3:]  # 去掉 re: 前缀
                                try:
                                    pattern = re.compile(raw_pattern)
                                    self.pattern_to_primary.append((pattern, primary))
                                except re.error:
                                    pass  # 忽略非法正则表达式
                        # 主名称也作为自己的别名加入映射
                        self.alias_to_primary[primary] = primary

    def get(self, name: str):
        """
        根据主名称获取所有别名集合
        """
        return self.primary_to_aliases.get(name, set())

    def get_primary(self, name: str):
        """
        根据别名获取主名称
        """
        # 先尝试直接查找别名映射，如果失败则尝试正则模式匹配
        primary_name = self.alias_to_primary.get(name, None) or self.get_primary_by_pattern(name)
        # 如果仍未找到，则尝试使用格式化后的名称查找
        if primary_name is None:
            alias_format_name = format_name(name)
            primary_name = self.alias_to_primary.get(alias_format_name, name)
        return primary_name

    def get_primary_by_pattern(self, name: str):
        """
        使用正则表达式匹配别名，获取主名称
        """
        for pattern, primary in self.pattern_to_primary:
            if pattern.search(name):
                return primary
        return None

    def set(self, name: str, aliases: set[str]):
        """
        设置主名称及其别名集合
        """
        # 如果该主名称已有别名，则清除旧的别名映射
        if name in self.primary_to_aliases:
            for alias in self.primary_to_aliases[name]:
                self.alias_to_primary.pop(alias, None)
        # 更新主名称到别名集合的映射
        self.primary_to_aliases[name] = set(aliases)
        # 更新别名到主名称的映射
        for alias in aliases:
            self.alias_to_primary[alias] = name

            # ✅ 如果别名以 re: 开头，则视为正则表达式
            if alias.startswith("re:"):
                raw_pattern = alias[3:]
                try:
                    pattern = re.compile(raw_pattern)
                    self.pattern_to_primary.append((pattern, name))
                except re.error:
                    pass
        # 主名称也作为自己的别名加入映射
        self.alias_to_primary[name] = name
