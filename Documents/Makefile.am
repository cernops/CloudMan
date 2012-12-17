docdir = ${prefix}/usr/share/doc/cloudman/Betelgeuze
doc_DATA = design.pdf

all: design.pdf

design.pdf:
	cd DesignPhase2 ; latex design.tex  ; latex design.tex; latex design.tex ; dvipdf design.dvi ; mv design.pdf ..

clean:
	rm *.pdf
	cd Design  ; rm -f *~ *.pdf *.dvi *.ps *.aux *.toc *.lof
