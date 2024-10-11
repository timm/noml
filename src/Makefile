SHELL:= /bin/bash#
.SILENT: # no output

LOUD = \033[1;34m#
HIGH = \033[1;33m#
SOFT = \033[0m#

MUST  = lua gawk pandoc
MAYBE = watch figlet htop ranger ncdu bat tree vim a2ps ghostscript
#SILLY = tty-clock ../etc/bsdgames-osx.rb

Pandoc =                     \
 -s                           \
 --css my.css                  \
 -f markdown                    \
 --mathjax                       \
 -H ../etc/favicon.html           \
 --include-before=../etc/head.html \
 --include-after=../etc/foot.html   \
 --highlight-style kate 

help: ## show help
	grep '^[a-z].*:.*##' $(MAKEFILE_LIST) \
	| sort \
	| gawk 'BEGIN {FS="##"; print "\n$(LOUD)make$(SOFT) [OPTIONS]\n"} \
	              {sub(/:.*/,"",$$1); \
                 printf("$(LOUD)%10s$(SOFT) %s\n",$$1,$$2)}'
	echo -e "$(HIGH)"; cat ../etc/frog.txt; echo -e "$(SOFT)"

mac: setup ## mac os/x install instructions
	brew install -q $(MUST) $(MAYBE) $(SILLY)

vim: ## vim install
	mkdir -p ~/.vim
	if [[ ! -d ~/.vim/bundle ]]; \
	then git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim; \
	fi
	vim +'PluginInstall --sync' +qa

setup: ## set file permissions
	git config pull.rebase false

sh: ## run a shell
	bash --init-file  ../etc/dotbashrc -i

robots: ## exterminate!!
		/opt/homebrew/opt/bsdgames-osx/bin/robots

push: ## commit to main
	- echo -en "$(LOUD)Why this push? $(SOFT)" ;  read x ; git commit -am "$$x" ;  git push
	- git status

~/tmp/%.html : %.py
	echo "$@..."
	sed 's/--------.*//' $^ > ~/tmp/$<
	(cd ~/tmp; pycco -d . $<; echo "h2 { padding-top:5px; border-top: 1px solid #CCC; }" >> pycco.css)

all: ../src/*.lua ../docs/*.html setup

%.awk : %.mkd         
	1>&2 echo "... $@"
	gawk -f ../etc/md2awk.awk $< > $@

pretty:
	autopep8 -i --max-line-length 150 -a --indent-size 2 h2c.py

%.lua : %.md           
	1>&2 echo "... $@"
	gawk -f ../etc/md2lua.awk $< > $@
	luac -p $@

../docs/index.html : ../src/noml.md 
	1>&2 echo "... $@"
	sed -e '1d' -e '2d' $< | pandoc  -o $@ $(Pandoc)

../docs/%.html : ../src/%.md    
	1>&2 echo "... $@"
	sed -e '1d' -e '2d' $< | pandoc  -o $@ $(Pandoc)

../docs/%.html : ../src/%.py
	echo "$< ... "
	gawk -f etc/py2html.awk $< | pandoc $(Pandoc) -o $@

~/tmp/%.pdf: %.py  ## make doco: .py ==> .pdf
	mkdir -p ~/tmp
	echo "pdf-ing $@ ... "
	a2ps                 \
		-Br                 \
		--chars-per-line=100 \
		--file-align=fill      \
		--line-numbers=1        \
		--pro=color               \
		--left-title=""            \
		--borders=no             \
	    --left-footer="$<  "               \
	    --right-footer="page %s. of %s#"               \
		--columns 3                 \
		-M letter                     \
	  -o	 $@.ps $<
	ps2pdf $@.ps $@; rm $@.ps
	open $@


heading:
	- echo -en "$(LOUD)Heading? $(SOFT)" ;  read x ; figlet -W -f mini $$x | gawk '{print "#  " $$0}'

eg1:; python3 mink.py                                         -kmeans2  |sort -n |cat -n
ega:; python3 mink.py -t ../../moot/optimize/config/SS-A.csv  -kmeans2  |sort -n |cat -n
egb:; python3 mink.py -t ../../moot/optimize/config/SS-B.csv  -kmeans2  |sort -n |cat -n
egc:; python3 mink.py -t ../../moot/optimize/config/SS-C.csv  -kmeans2  |sort -n |cat -n
egd:; python3 mink.py -t ../../moot/optimize/config/SS-D.csv  -kmeans2  |sort -n |cat -n
ege:; python3 mink.py -t ../../moot/optimize/config/SS-E.csv  -kmeans2  |sort -n |cat -n
egf:; python3 mink.py -t ../../moot/optimize/config/SS-F.csv  -kmeans2  |sort -n |cat -n
egg:; python3 mink.py -t ../../moot/optimize/config/SS-G.csv  -kmeans2  |sort -n |cat -n

how20:
	$(foreach d,config hpo misc process, \
		$(foreach f,$(wildcard ../../moot/optimize/$d/*.csv), \
			 (python3.13 how.py -t $f --acquire &); ))
