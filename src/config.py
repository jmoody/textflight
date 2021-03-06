from pathlib import Path
from configparser import ConfigParser

VERSION = "0.3a"

config = ConfigParser()
config.read("./textflight.conf.example")
config.read("/etc/textflight.conf")
config.read(Path.home().joinpath(".config/textflight.conf"))
config.read(Path.home().joinpath("textflight.conf"))
config.read("./textflight.conf")

def get_section(name: str):
	return config[name]

def opendata(name: str):
	return open(Path(config["data"]["DataPath"]).joinpath(name), "r")

