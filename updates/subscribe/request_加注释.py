# 导入标准库和第三方库
from collections import defaultdict  # 用于嵌套字典结构
from concurrent.futures import ThreadPoolExecutor  # 用于多线程并发处理
from time import time  # 获取当前时间戳

from requests import Session, exceptions  # 用于 HTTP 请求
from tqdm.asyncio import tqdm_asyncio  # 异步进度条显示

# 导入项目内部模块
import utils.constants as constants
from utils.channel import format_channel_name  # 格式化频道名称
from utils.config import config  # 配置项
from utils.retry import retry_func  # 请求重试函数
from utils.tools import (
    merge_objects,  # 合并多个频道数据
    get_pbar_remaining,  # 获取进度条剩余时间
    get_name_url  # 从文本中提取频道名称和链接
)

# 异步函数：根据订阅链接列表获取频道数据
async def get_channels_by_subscribe_urls(
        urls,
        names=None,  # 可选频道名称过滤列表
        multicast=False,  # 是否为组播模式
        hotel=False,  # 是否为酒店模式
        retry=True,  # 是否启用重试机制
        error_print=True,  # 是否打印错误信息
        whitelist=None,  # 白名单列表
        callback=None,  # 回调函数用于进度通知
):
    """
    根据订阅链接获取频道列表
    """
    # 如果设置了白名单，则优先处理白名单中的链接
    if whitelist:
        urls.sort(key=lambda url: whitelist.index(url) if url in whitelist else len(whitelist))

    subscribe_results = {}  # 初始化结果字典
    subscribe_urls_len = len(urls)  # 总订阅链接数

    # 初始化异步进度条
    pbar = tqdm_asyncio(
        total=subscribe_urls_len,
        desc=f"Processing subscribe {'for multicast' if multicast else ''}",
    )
    start_time = time()  # 记录开始时间

    # 设置模式名称（组播/酒店/订阅）
    mode_name = "组播" if multicast else "酒店" if hotel else "订阅"

    # 如果有回调函数，通知开始处理
    if callback:
        callback(
            f"正在获取{mode_name}源, 共{subscribe_urls_len}个{mode_name}源",
            0,
        )

    hotel_name = constants.origin_map["hotel"]  # 获取酒店标识

    # 内部函数：处理单个订阅链接
    def process_subscribe_channels(subscribe_info: str | dict) -> defaultdict:
        region = ""
        url_type = ""

        # 如果是组播或酒店模式，并且传入的是字典格式
        if (multicast or hotel) and isinstance(subscribe_info, dict):
            region = subscribe_info.get("region")
            url_type = subscribe_info.get("type", "")
            subscribe_url = subscribe_info.get("url")
        else:
            subscribe_url = subscribe_info

        # 初始化频道数据结构（三层嵌套字典）
        channels = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        # 判断是否在白名单中
        in_whitelist = whitelist and (subscribe_url in whitelist)

        session = Session()  # 创建请求会话

        try:
            response = None

            # 发起请求（支持重试机制）
            try:
                response = (
                    retry_func(
                        lambda: session.get(
                            subscribe_url, timeout=config.request_timeout
                        ),
                        name=subscribe_url,
                    )
                    if retry
                    else session.get(subscribe_url, timeout=config.request_timeout)
                )
            except exceptions.Timeout:
                print(f"Timeout on subscribe: {subscribe_url}")

            # 如果请求成功
            if response:
                response.encoding = "utf-8"  # 设置编码
                content = response.text  # 获取响应内容

                # 判断是否为 M3U 格式
                m3u_type = True if "#EXTM3U" in content else False

                # 提取频道数据
                data = get_name_url(
                    content,
                    pattern=(
                        constants.multiline_m3u_pattern
                        if m3u_type
                        else constants.multiline_txt_pattern
                    ),
                    open_headers=config.open_headers if m3u_type else False
                )

                # 遍历频道项
                for item in data:
                    name = item["name"]
                    url = item["url"]

                    if name and url:
                        name = format_channel_name(name)  # 格式化频道名称

                        # 如果设置了频道过滤，只保留指定名称
                        if names and name not in names:
                            continue

                        # 分割 URL 和额外信息
                        url_partition = url.partition("$")
                        url = url_partition[0]
                        info = url_partition[2]

                        # 构造频道数据结构
                        value = url if multicast else {
                            "url": url,
                            "headers": item.get("headers", None),
                            "extra_info": info
                        }

                        # 如果在白名单中，标记来源
                        if in_whitelist:
                            value["origin"] = "whitelist"

                        # 如果是酒店模式，添加区域信息
                        if hotel:
                            value["extra_info"] = f"{region}{hotel_name}"

                        # 将频道数据加入 channels 字典
                        if name in channels:
                            if multicast:
                                if value not in channels[name][region][url_type]:
                                    channels[name][region][url_type].append(value)
                            elif value not in channels[name]:
                                channels[name].append(value)
                        else:
                            if multicast:
                                channels[name][region][url_type] = [value]
                            else:
                                channels[name] = [value]

        except Exception as e:
            if error_print:
                print(f"Error on {subscribe_url}: {e}")
        finally:
            session.close()  # 关闭请求会话
            pbar.update()  # 更新进度条

            # 回调通知剩余任务和预计时间
            remain = subscribe_urls_len - pbar.n
            if callback:
                callback(
                    f"正在获取{mode_name}源, 剩余{remain}个{mode_name}源待获取, 预计剩余时间: {get_pbar_remaining(n=pbar.n, total=pbar.total, start_time=start_time)}",
                    int((pbar.n / subscribe_urls_len) * 100),
                )

            return channels  # 返回频道数据

    # 使用线程池并发处理所有订阅链接
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(process_subscribe_channels, subscribe_url)
            for subscribe_url in urls
        ]
        for future in futures:
            subscribe_results = merge_objects(subscribe_results, future.result())

    pbar.close()  # 关闭进度条
    return subscribe_results  # 返回最终结果
