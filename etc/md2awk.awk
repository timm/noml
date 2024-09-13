BEGIN            { FS="[ (]"
                   pre= "# " }
/^%/             { $0 = "# " $0 }
NR==1            { print "#!/usr/bin/env gawk -f"; next }
NR==2            { print $0; next }
                 { gsub(/ _/," "Klass,$0) }
/^function /     { 
                   if ($2 ~ /[A-Z]+/) Klass = $2
                   gsub(/\?/,"")
                   n = index($0,"(")
                   a = substr($0,1,n)
                   b = substr($0,n+1)
                   gsub(/[ ]*:[ ]*[^ ,\)]+/,"",b)
                   print a  b ; next}
sub(/```awk/,"") { pre="" }
sub(/```/,"")    { pre="# " }
pre==""          { $0 = gensub(/\.([^0-9\\*\\$\\+])([a-zA-Z0-9_]*)/, 
                                "[\"\\1\\2\"]","g", $0) }
                 { print pre $0 }
