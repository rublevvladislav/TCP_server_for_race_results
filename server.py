import argparse
import logging
import socket
import threading
import re

logging.basicConfig(filename='log',
                    filemode='a',
                    format='%(asctime)s, %(name)s %(levelname)s %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger('tcpserver')


def process_buffer(buffer):
    """" Split race results data by closing char ([CR]), split received data and
        if group_num == 00 print prettified one to the console """
    # Check if closing char ([CR]) already in buffer
    while '[CR]' in buffer:
        # Split the buffer by first closing char
        data, buffer = buffer.split('[CR]', 1)
        # Check that string in format: BBBBxNNxHH:MM:SS.zhqxGG
        # BBBB - player_num x - space NN - channel_id
        # HH - hours MM - minutes SS - seconds zhq - milliseconds
        # GG - group_num
        if re.match(r'\d{4}\s\w{2}\s\d{2}[:]\d{2}[:]\d{2}[.]\d{3}\s\d{2}', data):
            logger.info(data)
            player_num, channel_id, player_time, group_num = data.split(' ')
            if group_num == '00':
                print(f'спортсмен, нагрудный номер {player_num} '
                      f'прошёл отсечку {channel_id} в «{player_time[:-2]}»')
        else:
            logger.error(data + '[CR]' + buffer)
            raise ValueError("incorrect data format")
    return buffer


def threaded_server(connection):
    """ TCP Server that receives race results data and processes it """
    try:
        buffer_recv = ''
        # Main loop until get all data
        while True:
            # Receive data from client, 1024 bytes each
            chunk = connection.recv(1024)
            buffer_recv += str(chunk, 'utf-8')
            buffer_recv = process_buffer(buffer_recv)
            # If chunk is empty break main loop
            if not chunk:
                break
    finally:
        connection.close()


if __name__ == '__main__':
    # Initialize instance of an argument parser
    parser = argparse.ArgumentParser(description='TCP Server')
    parser.add_argument('host', help='IP')
    parser.add_argument('port', type=int, help='Port')
    # Get the arguments
    args = parser.parse_args()
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind to the port
    sock.bind((args.host, args.port))
    threads = []
    print('waiting for a connection')
    # Continuously listen for a client request and spawn a new thread to handle every client
    while True:
        try:
            # Wait for client connection.
            sock.listen(1)
            Client, address = sock.accept()
            print('connected to: ' + address[0] + ':' + str(address[1]))
            # Work with each client in a new thread
            thread = threading.Thread(target=threaded_server, args=(Client,))
            thread.start()
            threads.append(thread)
        except KeyboardInterrupt:
            print('the server is shutting down')
            break
    # When server ends (through user keyboard interrupt), wait until remaining threads finish
    for thread in threads:
        thread.join()
