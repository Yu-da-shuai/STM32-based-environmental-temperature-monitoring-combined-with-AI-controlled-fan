import socket #导入网络编程模块
ip = '127.0.0.1'
port = 8080
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((ip, port))  #绑定Ip和端口
server.listen(1)   #监听
print('等待客户端链接...')
conn, addr = server.accept()
print('客户端已链接...',addr)

while True:
    data = conn.recv(1024)
    if not data:
        break
    print("客户端发送：",data.decode('utf-8'))
    data_client = input("请输入你要发送给客户端的消息：")
    conn.send(data_client.encode('utf-8'))

conn.close()
server.close()
