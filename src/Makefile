SHELL:= /bin/bash#
.SILENT:

LOUD=\033[1;34m 
SOFT=\033[0m

MUST  = lua gawk pandoc
MAYBE = watch figlet htop ranger ncdu bat tree 
SILLY = tty-clock ../etc/bsdgames-osx.rb

Pandoc =           \
 -s                 \
 --css my.css        \
 -f markdown          \
 --mathjax             \
 -H ../etc/favicon.html \
 --include-before=../etc/head.html \
 --include-after=../etc/foot.html   \
 --highlight-style tango 

help: ## show help
	grep '^[a-z].*:.*##' $(MAKEFILE_LIST) \
	| sort \
	| gawk 'BEGIN {FS="##"; print "\n$(LOUD)make$(SOFT) [OPTIONS]\n"} \
	              {sub(/:.*/,"",$$1); \
                 printf("$(LOUD)%10s$(SOFT) %s\n",$$1,$$2)}'

mac: setup ## mac os/x install instructions
	brew install -q $(MUST) $(MAYBE) $(SILLY)

setup: ## set file permissions
	chmod +x ./lua
	[ -f "noml.lua" ] && chmod +x ./noml.lua

robots: ## exterminate!!
		/opt/homebrew/opt/bsdgames-osx/bin/robots

push: ## commit to main
	- echo -en "$(LOUD)Why this push? $(SOFT)"; read x; git commit -am "$$x"
	- git push; git status

all: ../src/*.lua ../docs/*.html setup

%.lua : %.md           
	echo "... $@"
	gawk -f ../etc/md2lua.awk $< > $@
	luac -p $@

../docs/index.html : ../src/noml.md 
	echo "... $@"
	 sed -e '1d' -e '2d' $< | pandoc  -o $@ $(Pandoc)

../docs/%.html : ../src/%.md    
	echo "... $@"
	sed -e '1d' -e '2d' $< | pandoc  -o $@ $(Pandoc)
