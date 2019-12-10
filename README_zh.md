# Encrypted-DNS
[![License](https://img.shields.io/github/license/Siujoeng-Lau/Encrypted-DNS.svg)](https://github.com/Siujoeng-Lau/Encrypted-DNS/blob/master/LICENSE)
[![Releases](https://img.shields.io/github/v/release/Siujoeng-Lau/Encrypted-DNS)](https://github.com/Siujoeng-Lau/Encrypted-DNS/releases)
[![Downloads](https://pepy.tech/badge/encrypted-dns)](https://pepy.tech/project/encrypted-dns)

Encrypted-DNS 是一个用于转发 DNS 请求的 DNS 服务器. 它支持 UDP, TCP, DNS-over-HTTPS, 以及 DNS-over-TLS 协议. 

它将会避免 DNS 污染和劫持, 缓存 DNS 请求, 屏蔽指定客户端, 以及对 DNS 请求进行分流.
   
语言: [English](https://github.com/Siujoeng-Lau/Encrypted-DNS/blob/master/README.md), [简体中文](https://github.com/Siujoeng-Lau/Encrypted-DNS/blob/master/README_zh.md).

### 安装

* 安装 [Python 3.7](https://www.python.org/downloads/).

* 使用 `pip` 安装 `encrypted-dns`.

```
$ python3 -m pip install encrypted-dns
```

* 生成并编辑配置文件.

```
$ sudo encrypted-dns
$ vim ~/.config/encrypted_dns/config.json
```

* 运行 Encrypted-DNS 服务器.

```
$ sudo encrypted-dns
```

* 测试 DNS 请求.

```
Linux or MacOS:
$ dig @127.0.0.1 www.google.com

Windows:
$ nslookup www.google.com 127.0.0.1
```

* 将设备的 DNS 地址改为 `127.0.0.1`.

### 配置

Encrypted-DNS 将会在程序目录中生成 JSON 格式的配置文件.

#### Upstream DNS (上游 DNS)

下面的 JSON 对象是一个典型的上游 DNS 配置.

Encrypted-DNS 支持以下协议: `udp`, `tcp`, `tls`, 和 `https`. 

你可以指定使用 DNS-over-HTTPS 和 DNS-over-TLS 协议的服务器的 IP 地址, 来避免 DNS 缓存污染.

```
"upstream_dns": [
    {
        "protocol": "https",
        "address": "cloudflare-dns.com",
        "ip": "1.0.0.1",
        "port": 443,
        "weight": 0,
        "enable_http_proxy": False,
        "proxy_host": "localhost",
        "proxy_port": 8001
    },
    {
        "protocol": "tls",
        "address": "dns.google",
        "ip": "8.8.4.4",
        "port": 853,
        "weight": 100
    },
    {
        "protocol": "udp",
        "address": "9.9.9.9",
        "port": 53,
        "weight": 0
    },
    {
        "protocol": "tcp",
        "address": "8.8.4.4",
        "port": 53,
        "weight": 0
    }
}
```

如果你指定了多个上游 DNS, Encrypted-DNS 将会对每一次请求采用"随机选择"或"加权随机选择"的方式来指定上游 DNS.

#### Bootstrap DNS Address (备用 DNS)

如果你没有指定 DNS-over-TLS 或 DNS-over-HTTPS 协议服务器的 IP 地址, Encrypted-DNS 将会向 Bootstrap DNS 服务器查询其对应地址.

```
"bootstrap_dns_address": {
    "address": "1.0.0.1",
    "port": 53
}
```

建议中国大陆的用户将其设置为位于中国境内的 DNS 服务器.

#### Client Blacklist (客户端黑名单)

Encrypted-DNS 将会屏蔽来自该列表内的 IP 地址的 DNS 请求.

```
"client_blacklist": [
    "1.0.0.1",
    "172.100.100.100"
]
```

#### DNS Bypass (绕过指定域名)

Encrypted-DNS 不会把对该列表内的域名的 DNS 请求转发至上游 DNS.

请求将会被转发到 Bootstrap DNS Address (备用 DNS 服务器).

```
"dns_bypass": [
    "captive.apple.com",
    "connectivitycheck.gstatic.com",
    "detectportal.firefox.com",
    "msftconnecttest.com",
    "nmcheck.gnome.org",

    "pool.ntp.org",
    "time.apple.com",
    "time.asia.apple.com",
    "time.euro.apple.com",
    "time.nist.gov",
    "time.windows.com"
]
```

#### DNS Bypass China (绕过中国大陆域名)

如果开启此功能, Encrypted-DNS 将会把对于中国大陆域名的请求转发至 Bootstrap DNS Address (备用 DNS 服务器), 而将其他地区的域名转发至上游. 

```
"dns_bypass_china": true
```

#### DNS Cache (DNS 缓存)

如果开启此功能, Encrypted-DNS 将会依据 `TTL` 对请求结果进行缓存, 减少下次查询的延迟.
```
"enable_cache": true
```

#### Hosts

强制将指定域名解析到指定 IP 地址或别名.

```
"hosts": {
    "www.instagram.com": "31.13.82.174",
    "www.bbc.co.uk": "212.58.244.69"
}
```

#### Force SafeSearch (强制安全搜索)

强制对 Google, Bing, 和 Youtube 使用安全搜索模式, 过滤不良信息.

```
"force_safe_search": true
```

#### Block Ads (屏蔽广告)

屏蔽常见的广告域名.

```
"block_ads": true
```