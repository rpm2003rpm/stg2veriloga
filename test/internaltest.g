# STG file generated by Workcraft 3 (Return of the Hazard), version 3.3.3
.model intTest
.inputs in
.outputs out
.internal r1 r2
.graph
in+ r1+
in- r2-
out+ in-
out- in+
r1+ r2+
r1- out+
r2+ r1-
r2- out-
.marking {<out-,in+>}
.end
