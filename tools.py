from urllib.parse import urlparse

def checkurl(url):
    try:
        o = urlparse(url)
    except:
        raise BaseException("URL解析失败")
    if o.scheme != "http" and o.scheme != "https":
        raise BaseException("未添加协议或协议非http/https")
    if len(o.netloc) == 0:
        raise BaseException("域名或端口等错误")
    if o.path !=  '/' and len(o.path) != 0:
        raise BaseException("请勿包含路径")
    ws_scheme = ""
    if o.scheme == "http":
        ws_scheme = "ws"
    else:
        ws_scheme = "wss"
    return f"{o.scheme}://{o.netloc}/", f"{ws_scheme}://{o.netloc}/ws"

def test():
    print(checkurl("https://ops.naibahq.com/"))

if __name__ == '__main__':
    test()