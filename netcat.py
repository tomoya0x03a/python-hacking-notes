# 概要
#
# netcatの代替プログラム

import argparse
import locale
import os
import socket
import shlex
import subprocess
import sys
import textwrap
import threading


class NetCat:
    # NetCatクラスのコンストラクタ
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # メイン実行関数
    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    # データ送信関数
    def send(self):
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)

        try:
            while True:
                recv_len = 1
                response = ""
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                if response:
                    print(response)
                    buffer = input("> ")
                    buffer += "\n"
                    self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print("User terminated.")
            self.socket.close()
            sys.exit()
        except EOFError as e:
            print(e)

    # 通信待受関数
    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle,
                args=(client_socket,),
            )
            client_thread.start()

    # クライアント接続処理関数
    def handle(self, client_socket):
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())

        elif self.args.upload:
            file_buffer = b""
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break

            with open(self.args.upload, "wb") as f:
                f.write(file_buffer)
            message = f"Saved file {self.args.upload}"
            client_socket.send(message.encode())

        elif self.args.command:
            cmd_buffer = b""
            while True:
                try:
                    client_socket.send(b"<BHP: #>")
                    while "\n" not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())

                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b""

                except Exception as e:
                    print(f"server killed {e}")
                    self.socket.close()
                    sys.exit()


# コマンド実行関数
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return

    if os.name == "nt":
        shell = True
    else:
        shell = False

    # 外部コマンド実行
    output = subprocess.check_output(
        shlex.split(cmd), stderr=subprocess.STDOUT, shell=shell
    )

    # ロカールに応じた文字コードでデコード
    if locale.getdefaultlocale() == ("ja_JP", "cp932"):
        return output.decode("cp932")
    else:
        return output.decode()


if __name__ == "__main__":
    # コマンドライン引数解析器セットアップ
    parser = argparse.ArgumentParser(
        description="BHP Net Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """実行例:
            # 対話型コマンドシェルの起動
            netcat.py -t 192.168.1.108 -p 5555 -l -c
            # ファイルのアップロード
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt
            # コマンドの実行
            netcat.py -t 192.168.1.108 -p 5555 -l -e="cat /etc/passwd"
            # 通信先サーバーの135番ポートに文字列を送信
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135
            # サーバーに接続
            netcat.py -t 192.168.1.108 -p 5555"""
        ),
    )

    parser.add_argument(
        "-c",
        "--command",
        action="store_true",
        help="対話型シェルの初期化",
    )
    parser.add_argument(
        "-e",
        "--execute",
        help="指定コマンドの実行",
    )
    parser.add_argument(
        "-l",
        "--listen",
        action="store_true",
        help="通信待受モード",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="ポート番号の指定",
    )
    parser.add_argument(
        "-t",
        "--target",
        default="192.168.1.203",
        help="IPアドレスの指定",
    )
    parser.add_argument(
        "-u",
        "--upload",
        help="ファイルのアップロード",
    )

    # コマンドライン引数を解析
    args = parser.parse_args()
    if args.listen:
        buffer = ""
    else:
        buffer = sys.stdin.read()
    # NetCatクラスのインスタンス生成と実行
    nc = NetCat(args, buffer.encode())
    nc.run()
