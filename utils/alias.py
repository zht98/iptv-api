import os  # 文件路径和存在性检查
import re  # 正则表达式处理

import utils.constants as constants  # 项目常量定义
from utils.tools import get_real_path, resource_path, format_name  # 工具函数


class Alias:
    def __init__(self):
        self.primary_to_aliases: dict[str, set[str]] = {}  # 主名称 → 别名集合
        self.alias_to_primary: dict[str, str] = {}         # 别名 → 主名称
        self.pattern_to_primary: list[tuple[re.Pattern, str]] = []  # 正则 → 主名称

        # 获取别名配置文件路径
        real_path = get_real_path(resource_path(constants.alias_path))

        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                for line in f:
                    # 忽略空行、注释行和无效格式
                    if line.strip() and not line.startswith("#") and "," in line:
                        parts = [p.strip() for p in line.split(",")]
                        primary = parts[0]
                        aliases = set(parts[1:])
                        aliases.add(format_name(primary))  # 加入格式化主名称

                        self.primary_to_aliases[primary] = aliases

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

                        self.alias_to_primary[primary] = primary  # 主名称也作为别名

    def get(self, name: str):
        """
        获取主名称的所有别名集合
        """
        return self.primary_to_aliases.get(name, set())

    def get_primary(self, name: str):
        """
        根据别名获取主名称
        """
        # 先尝试直接查找
        primary_name = self.alias_to_primary.get(name, None)

        # 如果找不到，则尝试正则匹配
        if primary_name is None:
            primary_name = self.get_primary_by_pattern(name)

        # 如果仍未找到，尝试格式化名称查找
        if primary_name is None:
            alias_format_name = format_name(name)
            primary_name = self.alias_to_primary.get(alias_format_name, name)

        return primary_name

    def get_primary_by_pattern(self, name: str):
        """
        使用正则表达式匹配别名，获取主名称
        使用 re.search() 而非 re.match()
        """
        for pattern, primary in self.pattern_to_primary:
            if pattern.search(name):  # ✅ 使用 search 而不是 match
                return primary
        return None

    def set(self, name: str, aliases: set[str]):
        """
        设置主名称及其别名集合
        """
        if name in self.primary_to_aliases:
            for alias in self.primary_to_aliases[name]:
                self.alias_to_primary.pop(alias, None)

        self.primary_to_aliases[name] = set(aliases)

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

        self.alias_to_primary[name] = name
