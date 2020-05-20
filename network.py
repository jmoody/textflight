import select
import socket

import handler
from client import Client

ADDRESS = "::"
PORT = 10000
BUFFER_SIZE = 4096

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
		elif client.structure._destroyed:
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
		outputs = []
		for client in clients.copy():
			if len(client.write_buffer) > 0:
				outputs.append(client)
		inputs.append(ss)
		readable, writeable, exceptional = select.select(inputs, outputs, outputs)
		
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
				if not s in outputs:
					writeable.append(s)
		
		# Write to clients
		for s in writeable:
			if s in clients:
				client_write(s)
		
		# Disconnect quitting clients
		for s in clients:
			if s.quitting:
				s.sock.close()
				clients.remove(s)

