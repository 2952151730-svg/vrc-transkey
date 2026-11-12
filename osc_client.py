from pythonosc import udp_client

class VRCOSCClient:
    def __init__(self, ip: str = "127.0.0.1", port: int = 9000):
        self.ip = ip
        self.port = port
        self.client = udp_client.SimpleUDPClient(ip, port)

    def set_endpoint(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.client = udp_client.SimpleUDPClient(ip, port)

    def send_chatbox(self, text: str, direct_send: bool = True):
        """发送文本到 VRChat 头顶聊天框"""
        try:
            # VRChat OSC: /chatbox/input s b (text, send_immediately)
            self.client.send_message("/chatbox/input", [text, direct_send])
            print(f"[OSC] 发送成功 -> VRChat: {text}")
        except Exception as e:
            print(f"[OSC] 发送失败: {e}")

    def set_typing_status(self, is_typing: bool):
        """同步打字状态：角色头顶显示 ..."""
        try:
            self.client.send_message("/chatbox/typing", is_typing)
        except Exception as e:
            pass
