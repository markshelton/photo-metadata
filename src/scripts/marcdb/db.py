from elixir import metadata, session, setup_all, create_all, drop_all 
	
"""
a very slim wrapper around some elixir functions
to connect to, create, commit to and clean a marcdb
"""
	
def connect(uri):
	metadata.bind = uri
	setup_all()
	
def create():
	setup_all()
	create_all()
	
def commit():
	session.flush()
	session.clear()
	
def zap():
	drop_all()	