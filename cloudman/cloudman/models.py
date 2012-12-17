# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#	  * Rearrange models' order
#	  * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models
from django import forms

class ChangeLog(models.Model):
	id = models.IntegerField(primary_key=True)
	category = models.CharField(max_length=300)
	name = models.CharField(max_length=300)
	object_id = models.IntegerField()
	operation = models.CharField(max_length=300)
	comment = models.CharField(max_length=3000, blank=True)
	sys_comment = models.CharField(max_length=3000, blank=True)
	user = models.CharField(max_length=300)
	datetime = models.DateTimeField(auto_now=True)
	status = models.IntegerField()
	class Meta:
		db_table = u'changelog'

class Egroups(models.Model):
	name = models.CharField(max_length=40, primary_key=True)
	status = models.BooleanField(default=True)
	empty = models.BooleanField(default=False)
	def __unicode__(self):
		return self.name
	class Meta:
		db_table = u'egroups'

class Region(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(unique=True, max_length=50)
	description = models.CharField(max_length=100, blank=True)
	admin_group = models.ForeignKey(Egroups, null=True,db_column='admin_group', blank=True)
	#admin_group = models.ForeignKey(Egroups, null=True, blank=False)
	def __unicode__(self):
		   return u'%s %s %s' % (self.name, self.description, self.admin_group)
	class Meta:
		db_table = u'region'

class ResourceType(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(unique=True, max_length=50)
	resource_class = models.CharField(max_length=24)
	hepspecs = models.FloatField(null=True, blank=True)
	memory = models.FloatField(null=True, blank=True)
	storage = models.FloatField(null=True, blank=True)
	bandwidth = models.FloatField(null=True, blank=True)
	def __unicode__(self):
		retValue = (u' %s %s' %(self.name, self.resource_class))
		if self.hepspecs == None:
		   retValue = retValue + (u' %s' %(self.hepspecs))
		else:
		   retValue = retValue + (u' %f' %(self.hepspecs))
		if self.memory == None:
		   retValue = retValue + (u' %s' %(self.memory))
		else:
		   retValue = retValue + (u' %f' %(self.memory))
		if self.storage == None:
		   retValue = retValue + (u' %s' %(self.storage))
		else:
		   retValue = retValue + (u' %f' %(self.storage))
		if self.bandwidth == None:
		   retValue = retValue + (u' %s' %(self.bandwidth))
		else:
		   retValue = retValue + (u' %f' %(self.bandwidth))
		return retValue
	class Meta:
		db_table = u'resource_type'

class Zone(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(unique=True, max_length=50)
	description = models.CharField(max_length=100, blank=True)
	region = models.ForeignKey(Region, null=True, blank=True)
	hepspecs = models.FloatField(null=True, blank=True)
	memory = models.FloatField(null=True, blank=True)
	storage = models.FloatField(null=True, blank=True)
	bandwidth = models.FloatField(null=True, blank=True)
	hepspec_overcommit = models.FloatField(null=True, blank=True)
	memory_overcommit = models.FloatField(null=True, blank=True)
	def hepspectotal(self):
		spectotal = 0
		if ((self.hepspecs == None) or (self.hepspec_overcommit == None)):
		   return spectotal
		return self.hepspecs * self.hepspec_overcommit
	def memorytotal(self):
		memtotal = 0
		if ((self.memory == None) or (self.memory_overcommit == None)):
			return memtotal
		return self.memory * self.memory_overcommit
	def __unicode__(self):
		retValue = (u' %s %s %s' %(self.name, self.description, self.region))
		if self.hepspecs == None:
		   retValue = retValue + (u' %s' %(self.hepspecs))
		else:
		   retValue = retValue + (u' %f' %(self.hepspecs))
		if self.memory == None:
		   retValue = retValue + (u' %s' %(self.memory))
		else:
		   retValue = retValue + (u' %f' %(self.memory))
		if self.storage == None:
		   retValue = retValue + (u' %s' %(self.storage))
		else:
		   retValue = retValue + (u' %f' %(self.storage))
		if self.bandwidth == None:
		   retValue = retValue + (u' %s' %(self.bandwidth))
		else:
		   retValue = retValue + (u' %f' %(self.bandwidth))
		retValue = retValue + (u' %f %f' %(self.hepspec_overcommit, self.memory_overcommit))
		return retValue
	class Meta:
		db_table = u'zone'

class ZoneAllowedResourceType(models.Model):
	id = models.IntegerField(primary_key=True)
	zone = models.ForeignKey(Zone)
	resource_type = models.ForeignKey(ResourceType)
	def __unicode__(self):
		return u'%s %s' % (self.zone, self.resource_type)
	class Meta:
		db_table = u'zone_allowed_resource_type'

class Project(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(unique=True, max_length=50)
	description = models.CharField(max_length=100, blank=True)
	admin_group = models.CharField(max_length=40, blank=True)
	class Meta:
		db_table = u'project'

class Groups(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(unique=True, max_length=50)
	description = models.CharField(max_length=100, blank=True)
	admin_group = models.CharField(max_length=40, blank=True)
	def __unicode__(self):
		return u'%s %s %s' % (self.name, self.description, self.admin_group)
	class Meta:
		db_table = u'groups'

class TopLevelAllocation(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(unique=True, max_length=50)
	group = models.ForeignKey(Groups, null=True, blank=True)
	hepspec = models.FloatField(null=True, blank=True)
	memory = models.FloatField(null=True, blank=True)
	storage = models.FloatField(null=True, blank=True)
	bandwidth = models.FloatField(null=True, blank=True)
	def __unicode__(self):
		retValue = (u' %s %s' %(self.name, self.group))
		if self.hepspec == None:
		   retValue = retValue + (u' %s' %(self.hepspec))
		else:
		   retValue = retValue + (u' %f' %(self.hepspec))
		if self.memory == None:
		   retValue = retValue + (u' %s' %(self.memory))
		else:
		   retValue = retValue + (u' %f' %(self.memory))
		if self.storage == None:
		   retValue = retValue + (u' %s' %(self.storage))
		else:
		   retValue = retValue + (u' %f' %(self.storage))
		if self.bandwidth == None:
		   retValue = retValue + (u' %s' %(self.bandwidth))
		else:
		   retValue = retValue + (u' %f' %(self.bandwidth))
		return retValue
	class Meta:
		db_table = u'top_level_allocation'

class TopLevelAllocationAllowedResourceType(models.Model):
	id = models.IntegerField(primary_key=True)
	top_level_allocation = models.ForeignKey(TopLevelAllocation)
	zone = models.ForeignKey(Zone)
	resource_type = models.ForeignKey(ResourceType)
	def __unicode__(self):
		return u'%s %s %s' % (self.top_level_allocation, self.zone, self.resource_type)
	class Meta:
		db_table = u'top_level_allocation_allowed_resource_type'

class TopLevelAllocationByZone(models.Model):
	id = models.IntegerField(primary_key=True)
	top_level_allocation = models.ForeignKey(TopLevelAllocation)
	zone = models.ForeignKey(Zone)
	hepspec = models.FloatField(null=True, blank=True)
	memory = models.FloatField(null=True, blank=True)
	storage = models.FloatField(null=True, blank=True)
	bandwidth = models.FloatField(null=True, blank=True)

	def hepspec_fraction(self):
	   try:
		 if self.hepspec != None and self.zone.hepspecs != None:
			if self.zone.hepspecs == 0:
			   return 0
			else:
			   return "%.3f" % ( (self.hepspec/(self.zone.hepspecs * self.zone.hepspec_overcommit)) * 100 )
		 else:
			return ''
	   except ValueError:
		 return '' 

	def memory_fraction(self):
	   try:
		 if self.memory != None and self.zone.memory != None:
			if self.zone.memory == 0:
			   return 0
			else:
			   return "%.3f" % ( (self.memory/(self.zone.memory * self.zone.memory_overcommit)) * 100 )
		 else:
			return ''
	   except ValueError:
		 return ''

	def storage_fraction(self):
	   try:
		 if self.storage != None and self.zone.storage != None:
			if self.zone.storage == 0:
			   return 0
			else:
			   return "%.3f" % ( (self.storage/self.zone.storage) * 100 )
		 else:
			return ''
	   except ValueError:
		 return ''

	def bandwidth_fraction(self):
	   try:
		 if self.bandwidth != None and self.zone.bandwidth != None:
			if self.zone.bandwidth == 0:
			   return 0
			else:
			   return "%.3f" % ( (self.bandwidth/self.zone.bandwidth) * 100 )
		 else:
			return ''
	   except ValueError:
		 return ''

	def __unicode__(self):
		retValue = (u' %s' %(self.zone))
		if self.hepspec == None:
		   retValue = retValue + (u' %s' %(self.hepspec))
		else:
		   retValue = retValue + (u' %f' %(self.hepspec))
		if self.memory == None:
		   retValue = retValue + (u' %s' %(self.memory))
		else:
		   retValue = retValue + (u' %f' %(self.memory))
		if self.storage == None:
		   retValue = retValue + (u' %s' %(self.storage))
		else:
		   retValue = retValue + (u' %f' %(self.storage))
		if self.bandwidth == None:
		   retValue = retValue + (u' %s' %(self.bandwidth))
		else:
		   retValue = retValue + (u' %f' %(self.bandwidth))
		return retValue
	class Meta:
		db_table = u'top_level_allocation_by_zone'

class ProjectAllocation(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(unique=True, max_length=50)
	top_level_allocation = models.ForeignKey(TopLevelAllocation)
	project = models.ForeignKey(Project)
	group = models.ForeignKey(Groups)
	hepspec = models.FloatField(null=True, blank=True)
	memory = models.FloatField(null=True, blank=True)
	storage = models.FloatField(null=True, blank=True)
	bandwidth = models.FloatField(null=True, blank=True)
	def totalhepspec(self):  
	   try: 
		 if self.hepspec != None:
			return "%.3f" % (self.hepspec)
	   except ValueError:  
		 return '' 

	def totalmemory(self):					   
	   try: 
		 if self.memory != None:	  
			return "%.3f" % (self.memory)							
	   except ValueError:
		 return ''

	def totalstorage(self):						
	   try: 
		 if self.storage != None:	   
			return "%.3f" % (self.storage)							 
	   except ValueError:
		 return ''

	def totalbandwidth(self):					  
	   try: 
		 if self.bandwidth != None:		 
			return "%.3f" % (self.bandwidth)
	   except ValueError:
		 return ''

	def hepspec_fraction(self):
	   try:
		 if self.hepspec != None:
			if self.hepspec == 0:
			   return 0
			else:
			   return "%.3f" % ((self.hepspec/self.top_level_allocation.hepspec) * 100)		   
	   except ValueError:
		 return ''
   
	def memory_fraction(self):
	   try:
		 if self.memory != None:
			if self.memory == 0:
			   return 0
			else:
			   return "%.3f" % ((self.memory/self.top_level_allocation.memory) * 100)
	   except ValueError:
		 return ''

	def storage_fraction(self):
	   try:
		 if self.storage != None:
			if self.storage == 0:
			   return 0
			else:
			   return "%.3f" % ((self.storage/self.top_level_allocation.storage) * 100)
	   except ValueError:
		 return ''
  
	def bandwidth_fraction(self):
	   try:
		 if self.bandwidth != None:
			if self.bandwidth == 0:
			   return 0
			else:
			   return "%.3f" % ((self.bandwidth/self.top_level_allocation.bandwidth) * 100)
	   except ValueError:
		 return ''
	def __unicode__(self):
		retValue = (u' %s %s %s %s' %(self.name, self.top_level_allocation, self.project, self.group))
		if self.hepspec == None:
		   retValue = retValue + (u' %s' %(self.hepspec))
		else:
		   retValue = retValue + (u' %f' %(self.hepspec))
		if self.memory == None:
		   retValue = retValue + (u' %s' %(self.memory))
		else:
		   retValue = retValue + (u' %f' %(self.memory))
		if self.storage == None:
		   retValue = retValue + (u' %s' %(self.storage))
		else:
		   retValue = retValue + (u' %f' %(self.storage))
		if self.bandwidth == None:
		   retValue = retValue + (u' %s' %(self.bandwidth))
		else:
		   retValue = retValue + (u' %f' %(self.bandwidth))
		return retValue
	class Meta:
		db_table = u'project_allocation'

class ProjectAllocationAllowedResourceType(models.Model):
	id = models.IntegerField(primary_key=True)
	project_allocation = models.ForeignKey(ProjectAllocation)
	resource_type = models.ForeignKey(ResourceType)
	class Meta:
		db_table = u'project_allocation_allowed_resource_type'

class ProjectMetadata(models.Model):
	id = models.IntegerField(primary_key=True)
	project = models.ForeignKey(Project)
	attribute = models.CharField(max_length=50)
	value = models.CharField(max_length=100, blank=True)
	class Meta:
		db_table = u'project_metadata'

class ProjectAllocationMetadata(models.Model):
	id = models.IntegerField(primary_key=True)
	project = models.ForeignKey(Project)
	project_allocation = models.ForeignKey(ProjectAllocation)
	attribute = models.CharField(max_length=50)
	value = models.CharField(max_length=100, blank=True)
	class Meta:
		db_table = u'project_allocation_metadata'

class GroupAllocation(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(unique=True, max_length=50)
	group = models.ForeignKey(Groups)
	project_allocation = models.ForeignKey(ProjectAllocation, null=True, blank=True)
	parent_group_allocation = models.ForeignKey('self', null=True, blank=True)
	hepspec = models.FloatField()
	memory = models.FloatField()
	storage = models.FloatField()
	bandwidth = models.FloatField()
	def __unicode__(self):
		retValue = (u' %s %s %s %s' %(self.name, self.group, self.project_allocation, self.parent_group_allocation))
		if self.hepspec == None:
		   retValue = retValue + (u' %s' %(self.hepspec))
		else:
		   retValue = retValue + (u' %f' %(self.hepspec))
		if self.memory == None:
		   retValue = retValue + (u' %s' %(self.memory))
		else:
		   retValue = retValue + (u' %f' %(self.memory))
		if self.storage == None:
		   retValue = retValue + (u' %s' %(self.storage))
		else:
		   retValue = retValue + (u' %f' %(self.storage))
		if self.bandwidth == None:
		   retValue = retValue + (u' %s' %(self.bandwidth))
		else:
		   retValue = retValue + (u' %f' %(self.bandwidth))
		return retValue
	class Meta:
		db_table = u'group_allocation'

class GroupAllocationAllowedResourceType(models.Model):
	group_allocation = models.ForeignKey(GroupAllocation)
	resource_type = models.ForeignKey(ResourceType)
	class Meta:
		db_table = u'group_allocation_allowed_resource_type'

class GroupAllocationMetadata(models.Model):
	id = models.IntegerField(primary_key=True)
	group_allocation = models.ForeignKey(GroupAllocation)
	attribute = models.CharField(max_length=100)
	value = models.CharField(max_length=5000, blank=True)
	class Meta:
		db_table = u'group_allocation_metadata'

class UserGroupMapping(models.Model):
	user_name = models.CharField(max_length=50)
	group_name = models.CharField(max_length=100)
	class Meta:
		db_table = u'user_group_mapping'

class UserRoles(models.Model):
	user_name = models.CharField(max_length=50)
	sphere_type = models.CharField(max_length=20)
	sphere_name = models.CharField(max_length=50)
	role = models.CharField(max_length=50)
	class Meta:
		db_table = u'user_roles'

class ZoneFormValidate(forms.Form):
	region = forms.CharField(label="Region Name", max_length=50)
	name = forms.CharField(label="Zone Name", max_length=50)
	description = forms.CharField(label="Description",required=False, max_length=100)
	hepspecs = forms.FloatField(label="Hepspecs")
	memory = forms.FloatField(label="Memory (MB)")
	storage = forms.FloatField(label="Storage (MB)")
	bandwidth = forms.FloatField(label="Bandwidth (Mbps)")

