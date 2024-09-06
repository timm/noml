SHELL:= /bin/bash#
.SILENT:

LOUD=\033[1;34m 
SOFT=\033[0m

help: ##  show help
	grep '^[a-z].*:.*##' $(MAKEFILE_LIST) \
	| sort \
	| gawk 'BEGIN {FS="##"; print "\n$(LOUD)make$(SOFT) [OPTIONS]\n"} \
	              { sub(/^[^:]*:/,"",$$1); \
				          printf("$(LOUD)%10s$(SOFT) %s\n",$$1,$$2)}'

push: ##  commit to main
	git add *;git commit -am save;git push;git status


        #-H favicon.html         \
        #--css style.css \

Pandoc =           \
 -s                 \
 --css my.css        \
 -f markdown          \
 --mathjax             \
 --include-before=../etc/head.html \
 --include-after=../etc/foot.html   \
 --highlight-style tango 

../src/%.lua : ../docs/%.md 
	echo "$@ ... "
	gawk -f ../etc/md2lua.awk $< > $@

../docs/index.html : ../docs/noml.html
	echo "$@ ... "
	cp $< $@

../docs/%.html : ../docs/%.md  
	echo "$@ ... "
	cp ../etc/my.css ../docs/my.css
	sed -e '1d' -e '2d' $< | pandoc  -o $@ $(Pandoc)
