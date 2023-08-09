#  First example
# 
#  @author  Rodrigo Pedroso Mendes
#  @version V1.0
#  @date    10/02/23 01:11:41
#
#  #LICENSE# 
#    
#  Copyright (c) 2023 Rodrigo Pedroso Mendes
#
#  Permission is hereby granted, free of charge, to any  person   obtaining  a 
#  copy of this software and associated  documentation files (the "Software"), 
#  to deal in the Software without restriction, including  without  limitation 
#  the rights to use, copy, modify,  merge,  publish,  distribute, sublicense, 
#  and/or sell copies of the Software, and  to  permit  persons  to  whom  the 
#  Software is furnished to do so, subject to the following conditions:        
#   
#  The above copyright notice and this permission notice shall be included  in 
#  all copies or substantial portions of the Software.                         
#   
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,  EXPRESS OR 
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE  WARRANTIES  OF  MERCHANTABILITY, 
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
#  AUTHORS OR COPYRIGHT HOLDERS BE  LIABLE FOR ANY  CLAIM,  DAMAGES  OR  OTHER 
#  LIABILITY, WHETHER IN AN ACTION OF  CONTRACT, TORT  OR  OTHERWISE,  ARISING 
#  FROM, OUT OF OR IN CONNECTION  WITH  THE  SOFTWARE  OR  THE  USE  OR  OTHER  
#  DEALINGS IN THE SOFTWARE. 
#    
################################################################################

from vagen import *

#Create a module     
mod  = HiLevelMod("STG2VA_TB")
vdd  = mod.electrical(name = "vdd", direction = "inout")
in1  = mod.dig(domain = vdd, name = "in1",  direction = "output")
in2  = mod.dig(domain = vdd, name = "in2",  direction = "output")
rst  = mod.dig(domain = vdd, name = "rst",  direction = "output")
out1 = mod.dig(domain = vdd, name = "out1", direction = "input")
out2 = mod.dig(domain = vdd, name = "out2", direction = "input")
out3 = mod.dig(domain = vdd, name = "out3", direction = "input")
out4 = mod.dig(domain = vdd, name = "out4", direction = "input")

evnt1 = Cross(out1.diffHalfDomain, "both")
evnt2 = Cross(out2.diffHalfDomain, "both")
evnt3 = Cross(out3.diffHalfDomain, "both")
evnt4 = Cross(out4.diffHalfDomain, "both")

#First test sequence
mod.seq(True)(
    WaitUs(1),
    rst.write(True),
    WaitUs(1),
    While(True)(
        in1.write(True),
        WaitUs(7),
        in1.write(False),
        WaitUs(3),
        in1.write(True),
        WaitUs(3),
        in2.write(True),
        WaitUs(3),
        in1.write(False),
        in2.write(False),
        WaitUs(3),
        in2.write(True),
        WaitUs(7),
        in2.write(False),
        WaitUs(3),
        in2.write(True),
        WaitUs(3),
        in1.write(True),
        WaitUs(3),
        in1.write(False),
        in2.write(False),
        WaitUs(3)
    ) 
)

#Save veriloga file
file = open('veriloga.va', 'w')
file.write(mod.getVA())
file.close()

