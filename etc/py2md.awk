#!/usr/bin/env gawk -f
NR==1{ next}
NR==2{ next }
NR==3{ RS="^$"; next }
     { print prep($0) }

function prep(s) {
	sub(/\n#[^\n]*\n/,"")
	gsub(/\n\n"""/,"\n```\n\n",s)
	gsub(/"""\n\n/,"\n\n```python\n",s)
	return s}

