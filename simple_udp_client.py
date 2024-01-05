# 概要
#
# UDPクライアントの基本的な使い方を示す例

import socket

target_host = "127.0.0.1"
target_port = 9997

# ソケットオブジェクトの作成
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# データの送信
client.sendto(b"AAABBBCCC", (target_host, target_port))

# データの受信
data, address = client.recvfrom(4096)

print(data.decode("utf-8"))
print(address)

client.close()
