import select
import socket
import logging
import ssl

import handler
import config
from client import Client

netw = config.get_section("network")
ADDRESS = netw.get("Address")
PORT = netw.getint("Port")
BUFFER_SIZE = netw.getint("BufferSize")
SSL = netw.getboolean("SSL")
SSL_CERT_PATH = netw.get("SSLCert")
SSL_KEY_PATH = netw.get("SSLKey")

clients = []

def client_read(client):
	buf = client.sock.recv(BUFFER_SIZE)
	if len(buf) == 0:
		client.quitting = True
		return
	try:
		client.read_buffer+= buf.decode("utf-8")
	except UnicodeDecodeError:
		client.quitting = True
		return
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
	if len(client.write_buffer) > 0:
		client.write_buffer = client.write_buffer[client.sock.send(client.write_buffer):]

def init():
	
	# Load SSL context
	if SSL:
		ssl_context = ssl.SSLContext()
		ssl_context.load_cert_chain(certfile=SSL_CERT_PATH, keyfile=SSL_KEY_PATH)
	
	# Start socket server
	ss = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
	ss.setblocking(0)
	ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	ss.bind((ADDRESS, PORT))
	ss.listen()
	
	# Read from sockets
	while True:
		
		# Call select to get ready clients
		inputs = clients.copy()
		inputs.append(ss)
		readable, writeable, exceptional = select.select(inputs, [], clients)
		
		# Read from clients
		for s in (readable + exceptional):
			if s is ss:
				sock, addr = ss.accept()
				if SSL:
					try:
						sock = ssl_context.wrap_socket(sock, server_side=True)
					except ssl.SSLError as ex:
						logging.warning(str(ex))
						continue
				sock.setblocking(0)
				c = Client(sock)
				clients.append(c)
				logging.info("Client '%s' connected.", c.get_ip())
			else:
				client_read(s)
		
		# Write to clients
		for s in clients:
			client_write(s)
		
		# Disconnect quitting clients
		for s in clients:
			if s.quitting:
				if s.id != None:
					logging.info("Client '%s', logged in as %d, disconnected.", s.get_ip(), s.id)
				else:
					logging.info("Client '%s' disconnected.", s.get_ip())
				s.sock.close()
				clients.remove(s)

