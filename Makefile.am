PKGNAME = cloudman
VERSION = $(shell grep "%global Version" cloudman.spec |/bin/cut -d' ' -f3| /bin/sed -e 's/ //g')
RELEASE = $(shell grep "%global Release" cloudman.spec |/bin/cut -d' ' -f3| /bin/sed -e 's/ //g')
TARFILE=${PKGNAME}-${VERSION}-${RELEASE}.tar.gz

SUBDIRS     = cloudman doc export backends/LSF doc Documents

SOURCES=README AUTHORS autogen.sh ChangeLog configure.in cloudman.spec Makefile.am NEWS  TODO  COPYING INSTALL doc cloudman export backends Documents

####################################################################
# Prepare
####################################################################

prepare:
	@mkdir -p build/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

dist: prepare
	@tar  --gzip  --exclude CVS --exclude "*~" --exclude "#*" --exclude .git -cf build/${TARFILE} ${SOURCES}
	cp build/${TARFILE} .

all: dist

rpm: dist
	@rpmbuild --define "_topdir $(CURDIR)/build/" -ta build/${TARFILE}

sources: srpm

srpm: dist
	rpmbuild-md5 --define "dist .ai6" --define "_topdir $(CURDIR)/build/" -ts build/${TARFILE}

clean:
	rm -f ${TARFILE}
	rm -rf build

distclean: clean
	find . -name \*.pyc -exec rm -f \{} \;
	find . -name \*.pyo -exec rm -f \{} \;
	find . -name \*.pdf -exec rm -f \{} \;
####################################################################
# Documentation
####################################################################

doc: man html

man: prepare

html: prepare

