from fastapi import FastAPI, Request, WebSocket
from starlette.staticfiles import StaticFiles  # 挂载静态文件
from starlette.templating import Jinja2Templates
from agent import EnvironmentAgent
from fastapi.responses import HTMLResponse
import asyncio
from config import Config
import socket
import json
import threading
import uvicorn

app = FastAPI()
# 挂载一个静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")
# 设置模板文件
templates = Jinja2Templates(directory="templates")
# 全局变量，存储温湿度数据
# {'key':'value'}
environment_data = {
    "temperature": 0.0,
    "humidity": 0.0,
    "status": "正常"
}
# 硬件状态
hardware_connected = False
# TCP客户链接
tcp_clients = []
# 全局事件循环
event_loop = None


# WebSocket连接管理
class WebSocketManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        print(f"准备广播数据到{len(self.active_connections)}个客户端:{data}")
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
                print(f"成功向客户端发送数据")
            except Exception as e:
                print(f"向客户端发送数据时出错:{e}")
                self.disconnect(connection)


# 创建Websocket管理器
ws_manager = WebSocketManager()

# 初始化环境智能体
environment_agent = EnvironmentAgent()


# 返回Html页面，显示当前环境数据，跟路由
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html",{"request": request, "data": environment_data, "connected": hardware_connected})


@app.get("/data")
async def get_data():
    data = environment_data.copy()
    data["connected"] = hardware_connected
    return data


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json(environment_data)
        print(f"发送初始数据到了客户端：{environment_data}")
        # 保存到前事件循环
        global event_loop
        event_loop = asyncio.get_event_loop()
        print(f"websocket 连接已经建立，当前活动连接数：{len(ws_manager.active_connections)}")
        print(f"当前被捕获的事件循环:{event_loop}")

        # 保持连接
        while True:
            try:
                data = await websocket.receive_text()
                # 心跳检测 忽略心跳检测消息的日志记录,只记录实际的数据消息
                if data.strip() != "ping":
                    print(f"收到来自客户端的数据：{data}")
            except Exception as e:
                print(f"收到客户端的数据消息时出错:{e}")
                break
    except Exception as e:
        print(f"websocket连接时出错:{e}")
    finally:
        ws_manager.disconnect(websocket)
        print(f"websocket连接已关闭，当前活动连接数:{len(ws_manager.active_connections)}")


def tcp_server():
    """TCP服务器，用于接收硬件数据和发送指令"""
    global hardware_connected
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((Config.TCP_HOST, Config.TCP_PORT))
    server_socket.listen(5)

    print(f"TCP服务器已启动，监听 {Config.TCP_HOST}:{Config.TCP_PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        tcp_clients.append(client_socket)
        hardware_connected = True
        print(f"硬件连接成功: {addr}")
        # 广播硬件连接状态
        broadcast_connection_status()

        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                # 解析温湿度数据
                try:
                    print(f"原始数据: '{data}'")
                    # 处理多行数据
                    lines = data.split('\r\n')
                    print(f"解析到 {len([l for l in lines if l.strip()])} 行有效数据")
                    for i, line in enumerate(lines):
                        if line.strip():
                            print(f"处理第 {i + 1} 行数据: '{line}'")
                            # 解析 TEMP=%d,HUMI=%d 格式
                            temp_part, humi_part = line.split(',')
                            temperature = int(temp_part.split('=')[1])
                            humidity = int(humi_part.split('=')[1])

                            print(f"解析结果 - 温度: {temperature}°C, 湿度: {humidity}%")
                            # 创建传感器数据字典
                            sensor_data = {
                                'temperature': temperature,
                                'humidity': humidity
                            }

                            update_environment_data(sensor_data)
                            print(f"数据处理完成: {sensor_data}")
                except Exception as e:
                    print(f"数据解析错误: {e}, 原始数据: {data}")

        except Exception as e:
            print(f"连接错误: {e}")
        finally:
            client_socket.close()
            if client_socket in tcp_clients:
                tcp_clients.remove(client_socket)
            if not tcp_clients:
                hardware_connected = False
                # 广播硬件断开连接状态
                broadcast_connection_status()
            print(f"硬件断开连接: {addr}")

def update_environment_data(data):
    global environment_data
    print(f"接收到硬件数据：{data}")
    if 'temperature' in data:
        environment_data['temperature'] = float(data['temperature'])
    if 'humidity' in data:
        environment_data['humidity'] = float(data['humidity'])

    decision = environment_agent.make_decision(environment_data)
    environment_data['status'] = decision['status']

    if'command' in decision:
        send_command(decision['command'])
        #添加我们的指令信息到环境数据中，方便展示
        environment_data['command'] = decision['command']
    else:
        if 'command' in environment_data:
            del environment_data['command']
    print(f"环境数据更新完成：{environment_data}")

    #将硬件连接状态也发送给广播数据中
    broadcast_data = environment_data.copy()
    broadcast_data ['connected'] = hardware_connected
    #要广播数据到所有的socket连接中
    global event_loop
    if event_loop is not None:
        print(f"广播数据到所有的websocket连接中:{event_loop}")
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(broadcast_data),event_loop)
    else:
        print("未找到事件循环，无法广播数据")#

def broadcast_connection_status():
    global hardware_connected
    global event_loop

    #创建链接状态数据
    status_data = {
        'connected':hardware_connected,
        'temperature':environment_data['temperature'],
        'humidity':environment_data['humidity'],
        'status':environment_data['status']
    }
    if 'command' in environment_data:
        status_data['command'] = environment_data['command']
        print(f"广播硬件连接状态:{status_data}")

    if event_loop is not None:
        print(f"广播数据到所有websockt连接中:{event_loop}")
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(status_data),event_loop)
    else:
        print("未找到事件循环，无法广播数据")

def send_command(command)  :
    print(f"开始发送指令，当前硬件连接数：{len(tcp_clients)}")
    print(f"指令内容：{command}")
    for i ,client in enumerate(tcp_clients):
        try:
            client_addr = client.getpeername() if hasattr(client,'getpeername')else '未知地域'
            command_json = json.dumps(command)
            print(f"向硬件{client_addr}发送指令：{command_json}")
            client.sendall(command_json.encode("utf-8"))
            print(f"指令发送成功，已向硬件{client_addr}发送指令：{command_json}")
        except Exception as e:
            print(f"向硬件{client_addr}发送指令失败:{e}")
if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    tcp_thread = threading.Thread(target=tcp_server,daemon=True)
    tcp_thread.start()
    uvicorn.run(app,host=Config.FASTAPI_HOST,port=Config.FASTAPI_PORT)