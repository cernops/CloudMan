# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models

class AuthGroup(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=240)
    class Meta:
        db_table = u'auth_group'

class AuthGroupPermissions(models.Model):
    id = models.IntegerField(primary_key=True)
    group_id = models.IntegerField(unique=True)
    permission_id = models.IntegerField()
    class Meta:
        db_table = u'auth_group_permissions'

class AuthMessage(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    message = models.TextField()
    class Meta:
        db_table = u'auth_message'

class AuthPermission(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=150)
    content_type_id = models.IntegerField(unique=True)
    codename = models.CharField(unique=True, max_length=300)
    class Meta:
        db_table = u'auth_permission'

class AuthUser(models.Model):
    id = models.IntegerField(primary_key=True)
    username = models.CharField(unique=True, max_length=90)
    first_name = models.CharField(max_length=90)
    last_name = models.CharField(max_length=90)
    email = models.CharField(max_length=225)
    password = models.CharField(max_length=384)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    is_superuser = models.IntegerField()
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    class Meta:
        db_table = u'auth_user'

class AuthUserGroups(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField(unique=True)
    group_id = models.IntegerField()
    class Meta:
        db_table = u'auth_user_groups'

class AuthUserUserPermissions(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField(unique=True)
    permission_id = models.IntegerField()
    class Meta:
        db_table = u'auth_user_user_permissions'

class DjangoAdminLog(models.Model):
    id = models.IntegerField(primary_key=True)
    action_time = models.DateTimeField()
    user_id = models.IntegerField()
    content_type_id = models.IntegerField(null=True, blank=True)
    object_id = models.TextField(blank=True)
    object_repr = models.CharField(max_length=600)
    action_flag = models.IntegerField()
    change_message = models.TextField()
    class Meta:
        db_table = u'django_admin_log'

class DjangoContentType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=300)
    app_label = models.CharField(unique=True, max_length=300)
    model = models.CharField(unique=True, max_length=300)
    class Meta:
        db_table = u'django_content_type'

class DjangoFlatpage(models.Model):
    id = models.IntegerField(primary_key=True)
    url = models.CharField(max_length=300)
    title = models.CharField(max_length=600)
    content = models.TextField()
    enable_comments = models.IntegerField()
    template_name = models.CharField(max_length=210)
    registration_required = models.IntegerField()
    class Meta:
        db_table = u'django_flatpage'

class DjangoFlatpageSites(models.Model):
    id = models.IntegerField(primary_key=True)
    flatpage_id = models.IntegerField()
    site_id = models.IntegerField()
    class Meta:
        db_table = u'django_flatpage_sites'

class DjangoSession(models.Model):
    session_key = models.CharField(max_length=120, primary_key=True)
    session_data = models.TextField()
    expire_date = models.DateTimeField()
    class Meta:
        db_table = u'django_session'

class DjangoSite(models.Model):
    id = models.IntegerField(primary_key=True)
    domain = models.CharField(max_length=300)
    name = models.CharField(max_length=150)
    class Meta:
        db_table = u'django_site'

class Region(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=150)
    description = models.CharField(max_length=300, blank=True)
    admin_group = models.CharField(max_length=120, blank=True)
    class Meta:
        db_table = u'region'

class ResourceType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=150)
    class_field = models.CharField(max_length=24, db_column='class') # Field renamed because it was a Python reserved word.
    hepspecs = models.FloatField(null=True, blank=True)
    memory = models.FloatField(null=True, blank=True)
    storage = models.FloatField(null=True, blank=True)
    bandwidth = models.FloatField(null=True, blank=True)
    region = models.ForeignKey(Region, null=True, blank=True)
    class Meta:
        db_table = u'resource_type'

class Zone(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=150)
    description = models.CharField(max_length=300, blank=True)
    region = models.ForeignKey(Region, null=True, blank=True)
    hepspecs = models.FloatField(null=True, blank=True)
    memory = models.FloatField(null=True, blank=True)
    storage = models.FloatField(null=True, blank=True)
    bandwidth = models.FloatField(null=True, blank=True)
    hepspec_overcommit = models.FloatField(null=True, blank=True)
    memory_overcommit = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'zone'

class ZoneAllowedResourceType(models.Model):
    zone = models.ForeignKey(Zone)
    resource_type = models.ForeignKey(ResourceType)
    class Meta:
        db_table = u'zone_allowed_resource_type'

class Groups(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=150)
    description = models.CharField(max_length=300, blank=True)
    admin_group = models.CharField(max_length=120, blank=True)
    class Meta:
        db_table = u'groups'

class TopLevelAllocation(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=150)
    group = models.ForeignKey(Groups)
    hepspec = models.FloatField(null=True, blank=True)
    memory = models.FloatField(null=True, blank=True)
    storage = models.FloatField(null=True, blank=True)
    bandwidth = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'top_level_allocation'

class TopLevelAllocationAllowedResourceType(models.Model):
    top_level_allocation = models.ForeignKey(TopLevelAllocation)
    resource_type = models.ForeignKey(ResourceType)
    class Meta:
        db_table = u'top_level_allocation_allowed_resource_type'

class TopLevelAllocationByZone(models.Model):
    top_level_allocation = models.ForeignKey(TopLevelAllocation)
    zone = models.ForeignKey(Zone)
    hepspec_fraction = models.FloatField(null=True, blank=True)
    memory_fraction = models.FloatField(null=True, blank=True)
    storage_fraction = models.FloatField(null=True, blank=True)
    bandwidth_fraction = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'top_level_allocation_by_zone'

class Project(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=150)
    description = models.CharField(max_length=300, blank=True)
    admin_group = models.CharField(max_length=120, blank=True)
    class Meta:
        db_table = u'project'

class ProjectAllocation(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=150)
    top_level_allocation = models.ForeignKey(TopLevelAllocation)
    project = models.ForeignKey(Project)
    hepspec_fraction = models.FloatField(null=True, blank=True)
    memory_fraction = models.FloatField(null=True, blank=True)
    storage_fraction = models.FloatField(null=True, blank=True)
    bandwidth_fraction = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'project_allocation'

class ProjectAllocationAllowedResourceType(models.Model):
    project_allocation = models.ForeignKey(ProjectAllocation)
    resource_type = models.ForeignKey(ResourceType)
    class Meta:
        db_table = u'project_allocation_allowed_resource_type'

class ProjectMetadata(models.Model):
    project = models.ForeignKey(Project)
    attribute = models.CharField(max_length=150, primary_key=True)
    value = models.CharField(max_length=300, blank=True)
    class Meta:
        db_table = u'project_metadata'

class GroupAllocation(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=150)
    group = models.ForeignKey(Groups)
    project_allocation = models.ForeignKey(ProjectAllocation, null=True, blank=True)
    parent_group_allocation = models.ForeignKey('self', null=True, blank=True)
    hepspec_fraction = models.FloatField()
    memory_fraction = models.FloatField()
    storage_fraction = models.FloatField()
    bandwidth_fraction = models.FloatField()
    class Meta:
        db_table = u'group_allocation'

class GroupAllocationAllowedResourceType(models.Model):
    group_allocation = models.ForeignKey(GroupAllocation)
    resource_type = models.ForeignKey(ResourceType)
    class Meta:
        db_table = u'group_allocation_allowed_resource_type'

class GroupAllocationMetadata(models.Model):
    group_allocation = models.ForeignKey(GroupAllocation)
    attribute = models.CharField(max_length=150, primary_key=True)
    value = models.CharField(max_length=300, blank=True)
    class Meta:
        db_table = u'group_allocation_metadata'

class UserGroupMapping(models.Model):
    user_name = models.CharField(max_length=150, primary_key=True)
    group_name = models.CharField(max_length=300, primary_key=True)
    class Meta:
        db_table = u'user_group_mapping'

class UserRoles(models.Model):
    user_name = models.CharField(max_length=150, primary_key=True)
    sphere_type = models.CharField(max_length=60, primary_key=True)
    sphere_id = models.IntegerField(primary_key=True)
    role = models.CharField(max_length=150, primary_key=True)
    class Meta:
        db_table = u'user_roles'

