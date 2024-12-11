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

~/tmp/%.html : %.lua
	pycco -d ~/tmp $^
	echo "p { text-align: right; }" >> ~/tmp/pycco.css
	open $@

../docs/%.html : ../src/%.py
	echo "$< ... "
	gawk -f etc/py2html.awk $< | pandoc $(Pandoc) -o $@

~/tmp/ez.pdf : ez.lua  ## make pdf
	@mkdir -p docs
	@echo "pdf-ing $@ ... "
	@a2ps -b    -q                        \
		--chars-per-line=90 \
    --left-title="" \
    --right-title="" \
	  -A virtual  \
		--line-numbers=1                    \
		--highlight-level=normal  \
		--columns 3                 \
		--borders=no --pro=color --columns 3 \
		--pretty-print=../etc/lua.ssh             \
		--footer=""                     \
		-M letter -o $@.ps ez*.lua
	@ps2pdf $@.ps $@; rm $@.ps

~/tmp/%.pdf : %.lua  ## make pdf
	@mkdir -p docs
	@echo "pdf-ing $@ ... "
	@a2ps -Bjr    -q                        \
		--chars-per-line=90 \
		--line-numbers=1                    \
		--highlight-level=normal  \
		--columns 3                 \
		--borders=no --pro=color --columns 3 \
		--right-footer="" --left-footer=""    \
		--pretty-print=../etc/lua.ssh             \
		--footer="page %p."                     \
		-M letter -o $@.ps $<
	@ps2pdf $@.ps $@; rm $@.ps

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

  #     1  2   3   4    5 6 7  8   9    10    11   12  13   14    15  16 
acts:
	echo "lt,eq,stop,rows,x,y,n,asIs,toBe,rand,eps0,eps1,eps2,liked,ms,file"
	mkdir -p ~/tmp/$(Act)
	rm ~/tmp/$(Act)/*.csv
	$(foreach d,misc hpo config process, \
		  $(foreach f,$(wildcard ../../moot/optimize/$d/*.csv), \
			   ((python3.13 how.py  -t $f --$(Act) | tee ~/tmp/$(Act)/$(notdir $f)) & ); ))

testlikes6:
	grep 'z 6' ~/tmp/likes.out |  gawk -F, '{print $$12,$$16,$$20,$$24}' | sort  | uniq -c

# timm@TIms-Mac-mini src % grep 'z 6' ~/tmp/likes.out | sed 's/,//g' | gawk '{print $12,$16,$20}' | sort  | uniq -c
#    6 False False False
#   33 False False Tru e
#    7 False True True
#    3 True True True
# timm@TIms-Mac-mini src % grep 'z 12' ~/tmp/likes.out | sed 's/,//g' | gawk '{print $12,$16,$20}' | sort  | uniq -c
#    1 False False False
#   23 False False True
#    1 False True True
#    1 True False False
#    9 True False True
#    1 True True False
#   13 True True True
# timm@TIms-Mac-mini src % grep 'z 24' ~/tmp/likes.out | sed 's/,//g' | gawk '{print $12,$16,$20}' | sort  | uniq -c
#   14 False False True
#    1 False True True
#   16 True False True
#   18 True True True
# timm@TIms-Mac-mini src % grep 'z 48' ~/tmp/likes.out | sed 's/,//g' | gawk '{print $12,$16,$20}' | sort  | uniq -c
#    8 False False True
#    1 False True True
#   19 True False True
#   21 True True True
#
go:
	$(MAKE) Act=$(Act) acts | tee ~/tmp/$(Act).out

acquires:
	$(MAKE) Act=acquire acts | tee ~/tmp/acquires.out

acquiresTF:
	gawk '$$3== 24  {print $$1, $$2} ' ~/tmp/acquires.out | sort | uniq -c

# 	echo "2,4,6,8,10,12,14,16"
# 	echo "z,n,x,y,_,r,l,N"

likesX:
	cat ~/tmp/likes.out |		gawk -F,  \
		'$$2==6  {printf $$10 "," $$14} $$2==12 {printf "," $$14}  $$2==24 {printf "," $$14}\
     $$2==48 {print "," $$14 "," $$18 } ' 

likesR:
	cat ~/tmp/likes.out |		gawk -F,  \
		'$$2==6  {printf $$10 "," $$12} $$2==12 {printf "," $$12}  $$2==24 {printf "," $$12}\
     $$2==48 {print "," $$12 "," $$18 } ' 

# 		 | sort -t,  -n
#

acquiresR:
	 echo "asIs,6,12,24,48,l,liked"
	cat ~/tmp/acquires.out |		gawk \
		'$$3==4  {printf $$8 "," $$10} $$3==8 {printf "," $$10}  $$3==16 {printf "," $$10}\
     $$3==32 {printf "," $$10} $$3==64 {print "," $$10 "," $$11 "," $$14} ' \
		 | sort -t,  -n


acqs:
	mkdir -p ~/tmp
	echo "data,rows,x,y,asIs,a12,a25,a100,a200,,r12,r25,r100,r200" > ~/tmp/$@.csv
	for f in ../../moot/optimize/[chmp]*/*.csv; do (./how2.lua -t $$f --$@ &); done | tee -a ~/tmp/$@.csv

wlt:
	./how2.lua --acqs ../../moot/optimize/[chmp]*/*.csv | tee ~/tmp/wlt.out
