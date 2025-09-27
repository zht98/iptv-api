import os  # 文件路径和存在性检查
import re  # 正则表达式处理

import utils.constants as constants  # 项目常量定义
from utils.tools import get_real_path, resource_path, format_name  # 工具函数


class Alias:
    def __init__(self):
        # 主名称到别名集合的映射
        self.primary_to_aliases: dict[str, set[str]] = {}
        # 别名到主名称的映射
        self.alias_to_primary: dict[str, str] = {}
        # 正则表达式模式到主名称的映射列表
        self.pattern_to_primary: list[tuple[re.Pattern, str]] = []

        # 获取别名配置文件的真实路径
        real_path = get_real_path(resource_path(constants.alias_path))

        # 如果文件存在，则读取并处理内容
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                for line in f:
                    # 忽略空行、注释行和无效格式行
                    if line.strip() and not line.startswith("#") and "," in line:
                        # 按逗号分割主名称和别名
                        parts = [p.strip() for p in line.split(",")]
                        primary = parts[0]
                        aliases = set(parts[1:])

                        # 将格式化后的主名称也加入别名集合
                        aliases.add(format_name(primary))
                        self.primary_to_aliases[primary] = aliases

                        # 遍历别名集合，建立映射关系
                        for alias in aliases:
                            self.alias_to_primary[alias] = primary

                            # ✅ 如果别名中包含 *，则视为正则表达式，直接编译
                            if '*' in alias:
                                try:
                                    pattern = re.compile(alias)
                                    self.pattern_to_primary.append((pattern, primary))
                                except re.error:
                                    pass  # 忽略非法正则表达式

                        # 主名称也作为自己的别名加入映射
                        self.alias_to_primary[primary] = primary

    def get(self, name: str):
        """
        获取某个主名称的所有别名集合
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

        # 如果仍未找到，尝试使用格式化名称查找
        if primary_name is None:
            alias_format_name = format_name(name)
            primary_name = self.alias_to_primary.get(alias_format_name, name)

        return primary_name

    def get_primary_by_pattern(self, name: str):
        """
        使用正则表达式匹配别名，获取主名称
        """
        for pattern, primary in self.pattern_to_primary:
            if pattern.match(name):
                return primary
        return None

    def set(self, name: str, aliases: set[str]):
        """
        设置主名称及其别名集合
        """
        # 清除旧的别名映射
        if name in self.primary_to_aliases:
            for alias in self.primary_to_aliases[name]:
                self.alias_to_primary.pop(alias, None)

        # 更新主名称到别名集合的映射
        self.primary_to_aliases[name] = set(aliases)

        # 更新别名到主名称的映射
        for alias in aliases:
            self.alias_to_primary[alias] = name

            # ✅ 如果别名中包含 *，则视为正则表达式，直接编译
            if '*' in alias:
                try:
                    pattern = re.compile(alias)
                    self.pattern_to_primary.append((pattern, name))
                except re.error:
                    pass

        # 主名称也作为自己的别名加入映射
        self.alias_to_primary[name] = name
