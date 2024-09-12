BEGIN            { pre="-- " }
/^%/             { $0 = "-- " $0 }
NR==1            { print "#!/usr/bin/env lua"; next }
NR==2            { print $0; next }
/^function /     { gsub(/\?/,"")
                   n=index($0,"(")
                   a=substr($0,1,n)
                   b=substr($0,n+1)
                   gsub(/[ ]*:[ ]*[^ ,\)]+/,"",b)
                   print a  b ; next}
sub(/```lua/,"") { pre="" }
sub(/```/,"")    { pre="-- " }
                 { print pre $0 }
