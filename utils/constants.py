import os      # 操作系统路径模块，用来拼接和处理文件路径
import re      # 正则表达式模块，用来定义和编译匹配模式

# 配置目录和输出目录
config_dir = "config"
output_dir = "output"

# 各类配置文件路径
live_path = os.path.join(config_dir, "live")              # 直播源配置目录
hls_path = os.path.join(config_dir, "hls")                # HLS 源配置目录
alias_path = os.path.join(config_dir, "alias.txt")        # 别名配置文件
epg_path = os.path.join(config_dir, "epg.txt")            # EPG 配置文件
whitelist_path = os.path.join(config_dir, "whitelist.txt")# 白名单文件
blacklist_path = os.path.join(config_dir, "blacklist.txt")# 黑名单文件
subscribe_path = os.path.join(config_dir, "subscribe.txt")# 订阅源文件

# 各类输出结果文件路径
epg_result_path = os.path.join(output_dir, "epg/epg.xml") # EPG XML 输出
epg_gz_result_path = os.path.join(output_dir, "epg/epg.gz") # 压缩 EPG 输出
ipv4_result_path = os.path.join(output_dir, "ipv4/result.txt") # IPv4 结果
ipv6_result_path = os.path.join(output_dir, "ipv6/result.txt") # IPv6 结果
live_result_path = os.path.join(output_dir, "live.txt")        # 直播结果
live_ipv4_result_path = os.path.join(output_dir, "ipv4/live.txt") # IPv4 直播结果
live_ipv6_result_path = os.path.join(output_dir, "ipv6/live.txt") # IPv6 直播结果
rtmp_data_path = os.path.join(output_dir, "data/rtmp.db")        # RTMP 数据库
hls_result_path = os.path.join(output_dir, "hls.txt")            # HLS 结果
hls_ipv4_result_path = os.path.join(output_dir, "ipv4/hls.txt")  # IPv4 HLS 结果
hls_ipv6_result_path = os.path.join(output_dir, "ipv6/hls.txt")  # IPv6 HLS 结果
cache_path = os.path.join(output_dir, "data/cache.pkl.gz")       # 缓存文件

# 日志文件路径
speed_test_log_path = os.path.join(output_dir, "log/speed_test.log") # 速度测试日志
result_log_path = os.path.join(output_dir, "log/result.log")         # 结果日志
statistic_log_path = os.path.join(output_dir, "log/statistic.log")   # 统计日志
nomatch_log_path = os.path.join(output_dir, "log/nomatch.log")       # 未匹配日志
log_path = os.path.join(output_dir, "log/log.log")                   # 通用日志

# URL 正则模式定义
url_host_pattern = re.compile(r"((webview|https?|rtmp|rtsp)://)?([^:@/]+(:[^:@/]*)?@)?(\[[0-9a-fA-F:]+]|([\w-]+\.)+[\w-]+)")   # 匹配 URL 主机部分，支持 webview/http/https/rtmp/rtsp 协议

url_pattern = re.compile(r"(?P<url>(?:webview://)?" + url_host_pattern.pattern + r"(?:\S*?(?=\?$|\?\$|$)|[^\s?]*))")   # 匹配完整 URL，允许 webview:// 前缀

rt_url_pattern = re.compile(r"^(rtmp|rtsp)://.*$")   # 匹配 RTMP/RTSP URL
rtp_pattern = re.compile(r"^(?P<name>[^,，]+)[,，]?(?P<url>rtp://.*)$") # 匹配 RTP URL

# 文本行匹配模式
demo_txt_pattern = re.compile(r"^(?P<name>[^,，]+)[,，]?(?!#genre#)" + r"(" + url_pattern.pattern + r")?")   # 演示用，URL 可选

txt_pattern = re.compile(r"^(?P<name>[^,，]+)[,，](?!#genre#)" + r"(" + url_pattern.pattern + r")")   # 标准行，必须有 URL

multiline_txt_pattern = re.compile(r"^(?P<name>[^,，]+)[,，](?!#genre#)" + r"(" + url_pattern.pattern + r")",
    re.MULTILINE)   # 多行文本匹配

# M3U 格式匹配模式
m3u_pattern = re.compile(r"^#EXTINF:-1[\s+,，](?P<attributes>[^,，]+)[，,](?P<name>.*?)\n" + r"(" + url_pattern.pattern + r")")

multiline_m3u_pattern = re.compile(r"^#EXTINF:-1[\s+,，](?P<attributes>[^,，]+)[，,](?P<name>.*?)\n(?P<options>(#EXTVLCOPT:.*\n)*?)" + r"(" + url_pattern.pattern + r")",re.MULTILINE)

# 键值对匹配模式
key_value_pattern = re.compile(r'(?P<key>\w+)=(?P<value>\S+)')

# 频道名清理正则（去掉多余符号/关键词）
sub_pattern = re.compile(r"-|_|\((.*?)\)|（(.*?)）|\[(.*?)]|「(.*?)」| |｜|频道|普清|标清|高清|HD|hd|超清|超高|超高清|4K|4k|中央|央视|电视台|台|电信|联通|移动")

# 替换字典（统一符号）
replace_dict = {
    "plus": "+",
    "PLUS": "+",
    "＋": "+",
}

# 地区列表
region_list = [
    "广东","北京","湖南","湖北","浙江","上海","天津","江苏","山东","河南",
    "河北","山西","陕西","安徽","重庆","福建","江西","辽宁","黑龙江","吉林",
    "四川","云南","香港","内蒙古","甘肃","海南","云南",
]

# 来源类型映射
origin_map = {
    "hotel": "酒店源",
    "multicast": "组播源",
    "subscribe": "订阅源",
    "online_search": "关键字源",
    "whitelist": "白名单",
    "local": "本地源",
}

# 其他配置
ipv6_proxy = "http://www.ipv6proxy.net/go.php?u="          # IPv6 代理地址
foodie_url = "http://www.foodieguide.com/iptvsearch/"      # 美食搜索地址
foodie_hotel_url = "http://www.foodieguide.com/iptvsearch/iptvhotel.php" # 酒店源搜索地址
waiting_tip = "📄结果将在更新完成后生成，请耐心等待..."   # 等待提示信息
