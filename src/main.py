#!/usr/bin/env python3

import logging
import random

import config

logc = config.get_section("logging")
log_level = 50 - logc.getint("LogLevel") * 10
log_file = logc.get("LogFile")
if log_file == "":
	log_file = None
logging.basicConfig(filename=log_file, level=log_level, format=logc.get("LogFormat"))

import translations
import database
import network
import system

random.seed()
network.init()
