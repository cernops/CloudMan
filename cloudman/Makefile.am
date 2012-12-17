#
# subdirectories
#
SUBDIRS = script etc

# other stuff
wwwdir = ${prefix}/var/www/cloudman
www_DATA = cloudman.wsgi *.py

# cloudman base stuff
cloudmandir=${wwwdir}/cloudman
cloudman_DATA = cloudman/*.py

cloudmanxdir=${wwwdir}/cloudman/xml
cloudmanx_DATA = cloudman/xml/*.py

# import tools
importdir=${wwwdir}/import
import_DATA = import/*.py

# ldap tools
ldapdir=${wwwdir}/ldapRoleCreator
ldap_DATA = ldapRoleCreator/*.py

ldaptdir=${wwwdir}/ldapRoleCreator/test
ldapt_DATA = ldapRoleCreator/test/*.py

ldaprdir=${wwwdir}/ldapRoleCreator/roleCreator
ldapr_DATA = ldapRoleCreator/roleCreator/*.py

ldapcdir=${wwwdir}/ldapRoleCreator/roleCreator/code
ldapc_DATA = ldapRoleCreator/roleCreator/code/*.py

# url 
urldir=${wwwdir}/url
url_DATA = url/*.py

# media
mediadir=${wwwdir}/media
media_DATA = media/*.png media/*.jpg media/*.css media/*.gif

imgdir=${mediadir}/images
img_DATA = media/images/*.jpg media/images/*.png media/images/*.gif

jsdir=${mediadir}/javascript
js_DATA = media/javascript/*.js

styledir=${mediadir}/stylesheet
style_DATA = media/stylesheet/*.css

webdir=${mediadir}/web
web_DATA = media/web/*.js

#
# templates
#
tpldir=${wwwdir}/templates
tpl_DATA = templates/*.html

tplbasedir=${tpldir}/base
tplbase_DATA = templates/base/*.html

tplregiondir=${tpldir}/region
tplregion_DATA = templates/region/*.html

tplzonedir=${tpldir}/zone
tplzone_DATA = templates/zone/*.html

tplresourcedir=${tpldir}/resourcetype
tplresource_DATA = templates/resourcetype/*.html

tplgroupdir=${tpldir}/group
tplgroup_DATA = templates/group/*.html

tplprojectdir=${tpldir}/project
tplproject_DATA = templates/project/*.html

tpltopdir=${tpldir}/toplevelallocation
tpltop_DATA = templates/toplevelallocation/*.html

tplgrpallocdir=${tpldir}/groupallocation
tplgrpalloc_DATA = templates/groupallocation/*.html

tplprjallocdir=${tpldir}/projectallocation
tplprjalloc_DATA = templates/projectallocation/*.html

tpllogdir=${tpldir}/log
tpllog_DATA = templates/log/*.html


#
# templatestags
#
tpltagdir=${wwwdir}/templatetags
tpltag_DATA = templatetags/*.py


clean:
	find . -name \*.pyc -exec rm -f \{} \;
	find . -name \*.pyo -exec rm -f \{} \;

