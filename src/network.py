import select
import socket
import logging
import ssl
import time

import handler
import config
from client import Client

netw = config.get_section("network")
ADDRESS = netw.get("Address")
PORT = netw.getint("Port")
TIMEOUT = netw.getfloat("Timeout")
RATELIMIT = netw.getfloat("Ratelimit")
MIN_SESSION = netw.getfloat("MinSession")
MAX_SESSION = netw.getfloat("MaxSession")
BUFFER_SIZE = netw.getint("BufferSize")
SSL = netw.getboolean("SSL")
SSL_CERT_PATH = netw.get("SSLCert")
SSL_KEY_PATH = netw.get("SSLKey")

clients = []

def client_read(client):
	try:
		buf = client.sock.recv(BUFFER_SIZE)
	except ssl.SSLError as e:
		if e.errno != ssl.SSL_ERROR_WANT_READ:
			raise
		logging.warning(str(ex))
		client.quitting = True
		return
	except Exception as ex:
		client.quitting = True
		return
	if len(buf) == 0:
		client.quitting = True
		return
	try:
		client.read_buffer+= buf.decode("utf-8")
		if type(client.sock) == ssl.SSLSocket:
			left = client.sock.pending()
			while client.sock.pending() > 0:
				buf = client.sock.recv(client.sock.pending())
				client.read_buffer+= buf.decode("utf-8")
		else:
			try:
				while len(buf) == BUFFER_SIZE:
					buf = client.sock.recv(BUFFER_SIZE)
					client.read_buffer+= buf.decode("utf-8")
			except BlockingIOError:
				pass
	except UnicodeDecodeError:
		logging.warning("Client %s sent invalid characters.", client.get_ip())
		client.quitting = True
		return
	except Exception as ex:
		logging.warning(str(ex))
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
		client.last_command = time.time()
		try:
			client.write_buffer = client.write_buffer[client.sock.send(client.write_buffer):]
		except Exception as ex:
			logging.warning(str(ex))
			client.quitting = True

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
		now = time.time()
		for s in (readable + exceptional):
			if s is ss:
				sock, addr = ss.accept()
				try:
					if SSL:
						sock = ssl_context.wrap_socket(sock, server_side=True)
					sock.setblocking(0)
					c = Client(sock)
					clients.append(c)
					logging.info("Client '%s' connected.", c.get_ip())
				except Exception as ex:
					logging.warning(str(ex))
					continue
			else:
				if now - s.last_command < RATELIMIT:
					s.quitting = True
					logging.warning("Client '%s' exceeded ratelimit.", c.get_ip())
				client_read(s)
		
		# Write to clients
		for s in clients:
			if now - s.last_command > TIMEOUT:
				s.quitting = True
				logging.warning("Client '%s' timed out.", c.get_ip())
			else:
				client_write(s)
		
		# Disconnect quitting clients
		for s in clients:
			if s.quitting:
				if s.id != None:
					logging.info("Client '%s', logged in as %d, disconnected.", s.get_ip(), s.id)
				else:
					logging.info("Client '%s' disconnected.", s.get_ip())
				session_length = now - s.session_start
				if session_length < MIN_SESSION or session_length > MAX_SESSION:
					logging.warning("Client '%s' exceeded allowed session bounds.", c.get_ip())
				try:
					s.sock.close()
				except Exception:
					pass
				clients.remove(s)

