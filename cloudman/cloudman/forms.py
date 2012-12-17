'''
Created on May 25, 2012 for easy code lookup models.py becomes very large
@author: Malik Ehsanullah
'''
from django import forms
from validator import validate_comment,validate_name,validate_descr
from models import Region,Groups,Project,TopLevelAllocation
from models import ProjectAllocation,GroupAllocation
from django.db.models import Q
class GroupsForm(forms.Form):
    name = forms.CharField(
                    label="Group Name",max_length=50, 
                    help_text="Enter Unique Name - Maximum of 50 Characters",validators = [validate_name] )
    description = forms.CharField(
                    label="Description of Group",required=False,max_length=100,
                    help_text='Brief Description of Group - Maximum of 100 Characters',validators = [validate_descr] )
    admin_group = forms.CharField(
                    label="Administrative E-Group",help_text="Enter an E-Group name or substring of atleast 4 character in the e-group name",validators = [validate_name] )
    comment = forms.CharField(
                    label="Comment",required=False,max_length=3000,
                    help_text='Enter Comments about the group(Useful for Logging)- Maximum of 3000 Characters', widget = forms.Textarea(attrs = {'cols':30,'rows':5}),
                    validators = [validate_comment] )
    
class ResourceTypeForm(forms.Form):
    name = forms.CharField(label="Resource Type Name", max_length=50,help_text="Enter Unique Name - Maximum of 50 Characters",
                    validators = [validate_name])
    resource_class = forms.ChoiceField(label="Resource Class", choices=(('virtual','virtual'),('physical','physical')),
                             help_text="Select one of the choice")
    hepspec = forms.FloatField(label="Capacity(HS06)", required=False, help_text="Total Resources Capacity(HS06) - If entered Positive Value greater than 0")
    memory = forms.FloatField(label="Memory (MB)",required=False, help_text="Total Available Memory in MB - Can be left blank")
    storage = forms.FloatField(label="Storage (MB)",required=False, help_text="Total Available Storage in MB - If entered Positive Value greater than 0")
    bandwidth = forms.FloatField(label="Bandwidth (Mbps)",required=False, help_text="Total Available Bandwidth in Mbps - Can be left blank")
    comment = forms.CharField(label="Comment",required=False, max_length=3000, help_text='Enter Comments about the resource type(Useful for Logging)- Maximum of 3000 Characters', widget = forms.Textarea(attrs = {'cols':30,'rows':5}),
                        validators = [validate_comment] )
    
class RegionForm(forms.Form):
    name = forms.CharField(label="Region Name", max_length=50, help_text="Enter Unique Name - Maximum of 50 Characters",
                    validators = [validate_name])
    description = forms.CharField(label="Description of Region",required=False, max_length=100, help_text='Brief Description of Region - Maximum of 100 Characters',
                            validators = [validate_descr] )
    admin_group = forms.CharField(label="Administrative E-Group", help_text="Enter an E-Group name",
                            validators = [validate_name] )
    comment = forms.CharField(label="Comment",required=False, max_length=3000, help_text='Enter Comments about the Region(Useful for Logging)- Maximum of 3000 Characters', widget = forms.Textarea(attrs = {'cols':30,'rows':5}),
                          validators = [validate_comment] )    

class ZoneForm(forms.Form):
    def __init__(self, *args, **kwargs):
        groupsList = kwargs.pop('userGroups')
        isUserSuperUser = kwargs.pop('superUserRights')
        super(ZoneForm, self).__init__(*args, **kwargs)
        if isUserSuperUser:
            self.fields.insert(0, 'region', forms.ModelChoiceField(queryset=Region.objects.all().values_list('name', flat=True)))
        else:
            qset = Q(admin_group__exact=groupsList[0])
            if len(groupsList) > 1:
                for group in groupsList[1:]:
                    qset = qset | Q(admin_group__exact=group)         
            self.fields.insert(0, 'region', forms.ModelChoiceField(queryset=Region.objects.filter(qset).values_list('name', flat=True)))
        self.fields['region'].help_text='Select a Region to add the Zone'
    name = forms.CharField(label="Zone Name", max_length=50, help_text="Enter Unique Name - Maximum of 50 Characters",
                   validators = [validate_name])
    description = forms.CharField(label="Description", max_length=100, help_text='Brief Description of Region - Maximum of 100 Characters',
                            validators = [validate_descr] )      
    hepspecs = forms.FloatField(label="Total Capacity (HS06)", help_text="Total Resources Capacity in HS06")
    memory = forms.FloatField(label="Total Memory (MB)", help_text="Total Available Memory in MB")
    storage = forms.FloatField(label="Total Storage (MB)", help_text="Total Available Storage in MB")
    bandwidth = forms.FloatField(label="Total Bandwidth (Mbps)", help_text="Total Available Bandwidth in Mbps")
    comment = forms.CharField(label="Comment",required=False, max_length=3000, help_text='Enter Comments about the zone(Useful for Logging)- Maximum of 3000 Characters', widget = forms.Textarea(attrs = {'cols':30,'rows':5}),
                      validators = [validate_comment] )

class ProjectForm(forms.Form):
    name = forms.CharField(label="Project Name", max_length=50, help_text="Enter Unique Name - Maximum of 50 Characters",
                           validators = [validate_name] )
    description = forms.CharField(label="Description of Project",required=False, max_length=100, help_text='Brief Description of Project - Maximum of 100 Characters',
                           validators = [validate_descr] )       
    admin_group = forms.CharField(label="Administrative E-Group", help_text="Enter an E-Group name or substring of atleast 4 character in the e-group name  Maximum of 40 characters",
                           validators = [validate_name] )       
    comment = forms.CharField(label="Comment",required=False, max_length=3000, help_text='Enter Comments about the project(Useful for Logging)- Maximum of 3000 Characters', widget = forms.Textarea(attrs = {'cols':30,'rows':5}),
                           validators = [validate_comment] )   


class TopLevelAllocationForm(forms.Form):
    name = forms.CharField(label="Allocation Name", max_length=50, help_text="Enter Unique Name - Maximum of 50 Characters")
    group = forms.ModelChoiceField(label="Group Name", help_text="Select a group from the drop down list", queryset=Groups.objects.values_list('name', flat=True),widget=forms.Select(attrs={'class':'selector'}))
    hepspecs = forms.FloatField(label="Hepspecs", help_text="Total Allocated CPU Resources in Hepspec")
    memory = forms.FloatField(label="Memory (MB)", help_text="Total Allocated Memory in MB")
    storage = forms.FloatField(label="Storage (MB)", help_text="Total Allocated Storage in MB")
    bandwidth = forms.FloatField(label="Bandwidth (Mbps)", help_text="Total Allocated Bandwidth in Mbps")




class ProjectAllocationForm(forms.Form):
    name = forms.CharField(label="Allocation Name", max_length=50, help_text="Enter Unique Name - Maximum of 50 Characters")
    def __init__(self, *args, **kwargs):
        groupsList = kwargs.pop('userGroups')
        isUserSuperUser = kwargs.pop('superUserRights')
        super(ProjectAllocationForm, self).__init__(*args, **kwargs)
        if isUserSuperUser:
           self.fields.insert(1, 'top_level_allocation', forms.ModelChoiceField(queryset=TopLevelAllocation.objects.values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'})))
           self.fields.insert(2, 'project', forms.ModelChoiceField(queryset=Project.objects.values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'})))
        else:
           groupQset = Q(group__admin_group__exact=groupsList[0])
           if len(groupsList) > 1:
              for group in groupsList[1:]:
                groupQset = groupQset | Q(group__admin_group__exact=group)
           projectQset = Q(admin_group__exact=groupsList[0])
           if len(groupsList) > 1:
              for group in groupsList[1:]:
                projectQset = projectQset | Q(admin_group__exact=group)
           self.fields.insert(1, 'top_level_allocation', forms.ModelChoiceField(queryset=TopLevelAllocation.objects.filter(groupQset).values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'})))
           self.fields.insert(2, 'project', forms.ModelChoiceField(queryset=Project.objects.filter(projectQset).values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'})))
        self.fields['top_level_allocation'].help_text='Select the Top Level Allocation from which this allocation needs to be drawn'
        self.fields['project'].help_text = 'Select the Project Name from the list'
    group = forms.ModelChoiceField(label="Group", help_text="Select the Group Name from the list", queryset=Groups.objects.values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'}))
    hepspecs = forms.FloatField(label="Hepspec", help_text="Total Allocated CPU Resources in Hepspec")
    memory = forms.FloatField(label="Memory (MB)", help_text="Total Allocated Memory in MB")
    storage = forms.FloatField(label="Storage (MB)", help_text="Total Allocated Storage in MB")
    bandwidth = forms.FloatField(label="Bandwidth (Mbps)", help_text="Total Allocated Bandwidth in Mbps")
    comment = forms.CharField(label="Comment",required=False, max_length=3000, help_text='Enter Comments about the project allocation(Useful for Logging)- Maximum of 3000 Characters', widget = forms.Textarea(attrs = {'cols':30,'rows':5}))



class GroupAllocationForm(forms.Form):
    name = forms.CharField(label="Allocation Name", max_length=50, help_text="Enter Unique Name - Maximum of 50 Character")
    group = forms.ModelChoiceField(label="Groups", help_text="Select the Group Name from the list", queryset=Groups.objects.values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'}))

    def __init__(self, *args, **kwargs):
        groupsList = kwargs.pop('userGroups')
        isUserSuperUser = kwargs.pop('superUserRights')
        super(GroupAllocationForm, self).__init__(*args, **kwargs)
        if isUserSuperUser:
           self.fields.insert(2, 'project_allocation', forms.ModelChoiceField(queryset=ProjectAllocation.objects.values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'})))
           self.fields.insert(3, 'parent_group_allocation', forms.ModelChoiceField(queryset=GroupAllocation.objects.values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'})))
        else:
           projectQset = Q(project__admin_group__exact=groupsList[0])
           if len(groupsList) > 1:
              for group in groupsList[1:]:
                projectQset = projectQset | Q(project__admin_group__exact=group)
           groupQset = Q(group__admin_group__exact=groupsList[0])
           if len(groupsList) > 1:
              for group in groupsList[1:]:
                groupQset = groupQset | Q(group__admin_group__exact=group)
           self.fields.insert(2, 'project_allocation', forms.ModelChoiceField(queryset=ProjectAllocation.objects.filter(projectQset).values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'})))
           self.fields.insert(3, 'parent_group_allocation', forms.ModelChoiceField(queryset=GroupAllocation.objects.filter(groupQset).values_list('name', flat=True), widget=forms.Select(attrs={'class':'selector'})))

        self.fields['project_allocation'].help_text='Select the Project Allocation from which this allocation needs to be drawn'
        self.fields['parent_group_allocation'].help_text = 'Select the Group Allocation from which this allocation needs to be drawn'
    hepspecs = forms.FloatField(label="Hepspec", help_text="Total Allocated CPU Resources in Hepspec")
    memory = forms.FloatField(label="Memory (MB)", help_text="Total Allocated Memory in MB")
    storage = forms.FloatField(label="Storage (MB)", help_text="Total Allocated Storage in MB")
    bandwidth = forms.FloatField(label="Bandwidth (Mbps)", help_text="Total Allocated Bandwidth in Mbps")






