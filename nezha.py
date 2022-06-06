import re
import socket
import requests
import websocket
import json
import pandas as pd
import humanize
from config import PermitTime

socket.setdefaulttimeout(15)

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
            raise BaseException(f"连接失败，请检查 {self.url} 是否可访问")
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
        except BaseException as e:
            self.ws.shutdown()
            raise BaseException(f"WebSocket连接失败，请检查 {self.ws_url}，错误信息: {str(e)}")
        try:
            res = json.loads(self.ws.recv())
            self.ws.shutdown()
            alive_count = 0
            MemTotal = 0
            NetInSpeedTotal = 0
            NetOutSpeedTotal = 0
            NetInTransferTotal = 0
            NetOutTransferTotal = 0
            now = pd.to_datetime(res['now'], unit='ms').value
            for i in res['servers']:
                if i['LastActive'] == "0001-01-01T00:00:00Z":
                    continue
                server_now = pd.to_datetime(i['LastActive'], format='%Y-%m-%dT%H:%M:%S.%f%z').value
                if now - server_now < PermitTime:
                    alive_count += 1
                else:
                    continue
                MemTotal += i['Host']['MemTotal']
                NetInSpeedTotal += i['State']['NetInSpeed']
                NetOutSpeedTotal += i['State']['NetOutSpeed']
                NetInTransferTotal += i['State']['NetInTransfer']
                NetOutTransferTotal += i['State']['NetOutTransfer']
            msg = f"WebSocket连接成功！\n" \
            f"获取到{len(res['servers'])}个服务器\n" \
            f"总在线服务器\t{alive_count}个\n" \
            f"总内存量\t{humanize.naturalsize(MemTotal, gnu=True)}\n" \
            f"总上行速度\t{humanize.naturalsize(NetOutSpeedTotal, gnu=True)}/s\n" \
            f"总下行速度\t{humanize.naturalsize(NetInSpeedTotal, gnu=True)}/s\n" \
            f"总上行流量\t{humanize.naturalsize(NetOutTransferTotal, gnu=True)}\n" \
            f"总下行流量\t{humanize.naturalsize(NetInTransferTotal, gnu=True)}"
            if NetOutTransferTotal !=0 and NetInTransferTotal !=0:
                msg += f"\n流量对等性\t{min(NetOutTransferTotal/NetInTransferTotal, NetInTransferTotal/NetOutTransferTotal)*100:.2f}%"
            return msg
        except:
            self.ws.shutdown()
            raise BaseException("WebSocket返回数据无法解析")

if __name__ == '__main__':
    n = NezhaDashboard("https://ops.naibahq.com/", "wss://ops.naibahq.com/ws")
    print(n.collect())
    