%global Basename cloudman
%global Version 0.1.7
%global Release 2

Summary: A high level Resource management tool
Name: %{Basename}
Version: %{Version}
Release: %{Release}%{?dist}
License: ASL 2.0
Group: Applications/Communications
URL: https://gitgw.cern.ch/gitweb/?p=cloudman.git
Source0: http://cern.ch/uschwick/software/%{Basename}-%{Version}-%{Release}.tar.gz
BuildRoot: %{_tmppath}/%{Basename}-%{version}-%{release}-buildroot
Requires: Django mysql httpd django-piston python-django-debug-toolbar python-matplotlib
BuildArch: noarch
BuildRequires: autoconf automake tetex ghostscript tetex-dvips texlive-latex
%description
A high level resource management tool.

%prep

%setup -qc

%build
./autogen.sh
%configure --prefix=/
make

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
mkdir -p 1777 %{buildroot}/var/www/tmp
mkdir -p 755 %{buildroot}/var/log/cloudman

%clean
rm -rf %{buildroot}

%post 
chown apache.apache /etc/cloudman/config
if [ -e /etc/sysconfig/httpd ] ; then
    echo "updating apache environment ... "
    cat /etc/sysconfig/httpd | grep -v MPLCONFIGDIR > /etc/sysconfig/httpd.new
    echo "export MPLCONFIGDIR=/var/tmp" >> /etc/sysconfig/httpd.new
    mv /etc/sysconfig/httpd.new /etc/sysconfig/httpd
    service httpd restart
fi

echo "Please edit /etc/cloudman/config now"
echo "When done run /usr/sbin/create_cloudman_ddb to create the cloudman ddb if necessary"
/bin/true

%files
%defattr(-,root,root,-)
%config(noreplace) /etc/cloudman/config
%config(noreplace) /etc/cloudman/db_schema_dump.sql  
%dir /var/www/tmp
%dir /var/log/cloudman
%config(noreplace)/etc/profile.d/cloudman.sh
%config(noreplace)/etc/profile.d/cloudman.csh
/var/www/cloudman/cloudman            
/var/www/cloudman/media                      
/var/www/cloudman/import
/var/www/cloudman/templates
/var/www/cloudman/templatetags
/var/www/cloudman/ldapRoleCreator
/var/www/cloudman/url
/var/www/cloudman/cloudman.wsgi
/var/www/cloudman/*.py
/var/www/cloudman/*.pyo
/var/www/cloudman/*.pyc
/var/www/export/export.wsgi
/var/www/export/*.py
/var/www/export/*.pyo
/var/www/export/*.pyc
/usr/sbin/create_cloudman_ddb
/etc/cron.daily/synchronize
/usr/share/cloudman/backends

%doc /usr/share/doc/cloudman/Betelgeuze/ReleaseNotes.pdf
%doc /usr/share/doc/cloudman/Betelgeuze/design.pdf


%changelog
* Tue  June 24 2014 <ulrich schwickerath at cern ch> 0.1.7-2
- fix path in wsgi file

* Fri  Oct 5 2012 <ulrich schwickerath at cern ch> 0.1.7-1
- update release 

* Tue  Jul 24 2012 <ulrich schwickerath at cern ch> 0.1.6-1
- add dependency on python-matplotlib 

* Tue  Jul 24 2012 <ulrich schwickerath at cern ch> 0.1.5-1
- several bug fixes

* Thu Jul 12 2012 <ulrich schwickerath at cern ch> 0.1.4-1
- add /var/log/cloudman
- set environement to run LSF import scripts

* Wed Jul 11 2012 <ehsan at barc gov in>  0.1.3-3
- branch off Aldebaran
- minor change to fix scrolling problem in the GUI

* Thu Jun 28 2012 <ulrich schwickerath at cern ch>  0.1.3-2 
- branch off Aldebaran
- minor change to checkout instructions in Release notes 

* Wed Jun 27 2012 <ulrich schwickerath at cern ch>  0.1.3-1
- iterate on documents

* Tue Jun 26 2012 <ulrich schwickerath at cern ch>  0.1.2-1
- add documentation
- packaging fixings to make rpmlint happy
- environment setup bug fixes

* Fri Jun 22 2012 <ulrich schwickerath at cern ch>  0.1.1-7
- export becomes a standalone application which can run on a different port
- simplify export and package it
- import missing files and directories into the rpm 
- rename CERN_LDAP_SERVER to LDAP_SERVER
- cleanup template config file

* Wed Jun 20 2012 <ulrich schwickerath at cern ch>  0.1.0-2
- new release
- add backend scripts for LSF
- move synchronization job to cron.hourly

* Wed May 23 2012 malik  0.0.10
- fix bug in project allocation queries

* Wed May 23 2012 Ulrich Schwickerath <ulrich schwickerath at cern ch>  0.0.9
- correct dependency on matplotlib 
- properly export variables for Django
- pickup all python files in the cloudman directory

* Tue May 22 2012  Ulrich Schwickerath <ulrich schwickerath at cern ch>  0.0.8
- fix dependency issue
- fix template directory location
- fix AI486
- fix AI497

* Mon May 21 2012  Ulrich Schwickerath <ulrich schwickerath at cern ch>  0.0.7
- new version
- import into git

* Tue Apr 24 2012  Ulrich Schwickerath <ulrich schwickerath at cern ch>  0.0.5 
- correct installation path
- fix database creation and config file permission

* Mon Apr 23 2012 Ulrich Schwickerath <ulrich schwickerath at cern ch>  0.0.3
- Initial build
- add configuration file 
- fix configuration file permissions
