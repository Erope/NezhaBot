import re
import requests
import websocket
import time
import json

class NezhaDashboard:
    def __init__(self, url, ws_url):
        self.url = url
        self.ws_url = ws_url
        self.s = requests.Session()
        self.ws = websocket.WebSocket()
        self.s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53'})
    
    def collect(self):
        res = f"正在对 {self.url} 检测...\n"
        self.init()
        self.checkpwd()
        self.checkfooter()
        res += f"面板版本为: {self.getversion()}\n"
        res += f"{self.checkws()}\n"
        res += "测试成功！"
        return res
        
    
    def init(self):
        try:
            html = self.s.get(self.url, timeout=10)
            html.encoding = "utf-8"
        except requests.exceptions.SSLError:
            raise BaseException("证书错误或其他原因导致SSLError")
        except:
            raise BaseException("连接失败，请检查 {self.url} 是否可访问")
        if html.status_code != requests.codes.ok:
            raise BaseException("非200响应，可能被防火墙拦截")
        self.html = html.text
    
    def checkpwd(self):
        if 'view-password' in self.html:
            raise BaseException("存在查看密码，无法继续，请关闭查看密码后再试")
        return
    
    def checkfooter(self):
        if 'naiba/nezha' not in self.html:
            raise BaseException("底部版权被修改或被防火墙拦截")
    
    def getversion(self):
        pattern = re.compile(r'v[0-9]+\.[0-9]+\.[0-9]+', re.I)
        m = pattern.search(self.html)
        if m is None:
            return "未知"
        if len(m.group(0)) > 9:
            return "未知"
        return m.group(0)
    
    def checkws(self):
        try:
            self.ws.connect(self.ws_url, timeout=10)
        except:
            self.ws.shutdown()
            raise BaseException("WebSocket连接失败，请检查 {self.ws_url}")
        try:
            res = json.loads(self.ws.recv())
            self.ws.shutdown()
            return f"WebSocket连接成功，获取到{len(res['servers'])}个服务器"
        except:
            self.ws.shutdown()
            raise BaseException("WebSocket返回数据无法解析")

if __name__ == '__main__':
    n = NezhaDashboard("https://ops.naibahq.com/", "wss://ops.naibahq.com/ws")
    print(n.collect())
    