from elixir import Entity, Field, ManyToOne, OneToMany, using_options
from datetime import datetime
import pymarc
	
class ControlField(Entity):
	tag = Field(TEXT)
	position = Field(Integer)
	record = ManyToOne('Record')
	value = Field(TEXT)
	using_options(tablename='control_fields')
	
class Record(Entity):
	leader = Field(TEXT)
	created = Field(DateTime, default=datetime.now)
	control_fields = OneToMany('ControlField', order_by='position')
	data_fields = OneToMany('DataField', order_by='position')
	using_options(tablename='records')
	
	def to_marc(self):
		r = pymarc.Record()
		r.leader
		for cf in self.control_fields:
			r.addField(pymarc.Field(tag=cf.tag, data=cf.value))
		for df in self.data_fields:
			f = pymarc.Field(tag=df.tag, indicators=[df.indicator1, df.indicator2])
			for sf in df.subfields:
				f.addSubfield(sf.code, sf.value)
			r.addField(f)
		return r.asMARC21()
	
class DataField(Entity):
	tag = Field(TEXT)
	indicator1 = Field(String(length=1))
	indicator2 = Field(String(length=1))
	position = Field(Integer)
	record = ManyToOne('Record')
	subfields = OneToMany('Subfield', order_by='position')
	using_options(tablename='data_fields')
	
	def __str__(self):
		s = "%s %s%s " % (self.tag, self.indicator1, self.indicator2)
		for sf in self.subfields:
			s += '$' + sf.code + sf.value
		return s
	
	
class Subfield(Entity):
	code = Field(String(length=1))
	value = Field(TEXT)
	position = Field(Integer)
	data_field = ManyToOne('DataField')
	using_options(tablename='subfields')