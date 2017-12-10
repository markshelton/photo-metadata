from pymarc import XmlHandler, parse_xml, MARCReader

from marcdb.db import connect, commit
from marcdb.models import ControlField, Record, DataField, Subfield
	
class Loader:
	
	def __init__(self, uri, verbose=False):
		self.verbose = verbose
		self.db = connect(uri)
	
	def load_xml(self, xml_file):
		handler = DatabaseHandler(verbose=self.verbose)
		parse_xml(xml_file, handler)
		commit()
	
	def load(self, marc_file):
		handler = DatabaseHandler(verbose=self.verbose)
		for record in MARCReader(file(marc_file)):
			handler.process_record(record)
		commit()
	
class DatabaseHandler(XmlHandler):
	"""
	Subclass of pymarc's XmlHandler to stream Record objects
	into the database using the process_record override.
	"""
	
	def __init__(self, verbose=False):
		self._record_count = 0
		self.verbose = verbose
	
	def process_record(self, marc_record):
		self._record_count += 1
		if self.verbose:
			print self._record_count
	
		r = Record()
		r.leader = marc_record.leader
		field_position = -1
		for marc_field in marc_record:
			field_position += 1
			if marc_field.is_control_field():
				f = ControlField()
				f.tag = marc_field.tag
				f.value = marc_field.data
				f.position = field_position
				r.control_fields.append(f)
			else:
				f = DataField()
				f.tag = marc_field.tag
				f.indicator1 = marc_field.indicators[0]
				f.indicator2 = marc_field.indicators[1]
				f.position = field_position
				subfield_position = -1
				for marc_subfield in marc_field:
					subfield_position += 1
					sf = Subfield()
					sf.code=marc_subfield[0]
					sf.value=marc_subfield[1]
					sf.position = subfield_position
					f.subfields.append(sf)
				r.data_fields.append(f)
	
		if self._record_count % 1000 == 0:
			commit()