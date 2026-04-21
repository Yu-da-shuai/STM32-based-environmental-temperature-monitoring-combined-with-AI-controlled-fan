import socket
ip = '127.0.0.1'
port = 8080
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((ip, port))

while True:
    msg = input('请输入你要发送的消息：')
    client.send(msg.encode('utf-8'))
    if  msg == 'exit':
        break
    data = client.recv(1024)
    print('接收到服务器发的消息为：',data.decode('utf-8'))

client.close()