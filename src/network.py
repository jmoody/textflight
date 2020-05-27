import select
import socket
import re

import handler
import config
from client import Client

netw = config.get_section("network")
ADDRESS = netw.get("Address")
PORT = netw.getint("Port")
BUFFER_SIZE = netw.getint("BufferSize")

clients = []

def client_read(client):
	buf = client.sock.recv(BUFFER_SIZE)
	if len(buf) == 0:
		clients.remove(client)
		client.sock.close()
		return
	client.read_buffer+= buf.decode("utf-8")
	index = client.read_buffer.find('\n')
	while index != -1:
		command = client.read_buffer[:index].strip().split(' ')
		if client.id == None:
			handler.handle_login(client, command[0], command[1:])
		elif client.structure == None or client.structure._destroyed:
			handler.handle_death(client)
		else:
			handler.handle_command(client, command[0], command[1:])
		client.read_buffer = client.read_buffer[index:].strip()
		index = client.read_buffer.find('\n')

def client_write(client):
	client.write_lock.acquire()
	client.write_buffer = client.write_buffer[client.sock.send(client.write_buffer):]
	client.write_lock.release()

def init():
	ss = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
	ss.setblocking(0)
	ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	ss.bind((ADDRESS, PORT))
	ss.listen()
	while True:
		
		# Call select to get ready clients
		inputs = clients.copy()
		inputs.append(ss)
		readable, writeable, exceptional = select.select(inputs, [], [])
		
		# Read from clients
		for s in readable:
			if s is ss:
				sock, addr = ss.accept()
				sock.setblocking(0)
				c = Client(sock)
				clients.append(c)
				writeable.append(c)
			else:
				client_read(s)
		
		# Write to clients
		for s in clients:
			client_write(s)
		
		# Disconnect quitting clients
		for s in clients:
			if s.quitting:
				s.sock.close()
				clients.remove(s)

