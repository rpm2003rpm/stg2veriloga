## @package stg
#  stg to verilogA converter
# 
#  @section license_main License
#
#  @author  Rodrigo Pedroso Mendes
#  @version V1.0
#  @date    14/02/23 13:37:31
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

#-------------------------------------------------------------------------------
# Import
#-------------------------------------------------------------------------------
import argparse
import re
from   vagen import *
from   grako import parse


#-------------------------------------------------------------------------------
## Parser Grammar
#
#-------------------------------------------------------------------------------
GRAMMAR = '''

    @@eol_comments :: /#.*?$\\n/
    @@whitespace :: /[\t ]+/
    @@grammar::Calc

    start   = stg $ ;

    stg     = {'\\n'}* '.model' name:name {'\\n'}+ 
              {input+:inputs        |  
               output+:outputs      | 
               internal+:internals  | 
               graph+:graph         |
               marking+:marking     |
               capacity+:capacity}* 
              '.end' {'\\n'}*; 

    inputs    = '.inputs'  {@+:name}+ {'\\n'}+;

    outputs   = '.outputs' {@+:name}+ {'\\n'}+;

    internals = '.internal' {@+:name}+ {'\\n'}+;

    dummy     = '.dummy'   {@+:name}+ {'\\n'}+;

    graph     = '.graph'   {'\\n'}+ {@+:tpLine}+ {'\\n'}*;

    tpLine    = {@+:tranPlace}+ {'\\n'}+;

    marking   = '.marking'  '{' {@+:unique}+ '}' {'\\n'}+;

    capacity  = '.capacity' {@+:unique}+ {'\\n'};

    unique    = implicit | explicit;

    explicit  = @+:name ['=' @+:value];
 
    implicit  = '<' @+:tranPlaceComma '>' ['=' @+:value];
     
    name      = /[a-zA-Z_][a-zA-Z_0-9.]*/;

    value     = /[0-9]*/;

    tranPlace = ?/[a-zA-Z_][a-zA-Z_0-9\+\-\~/.]*/?;

    tranPlaceComma = ?/[a-zA-Z_][a-zA-Z_0-9\+\-\~/.]*,[a-zA-Z_][a-zA-Z_0-9\+\-\~/.]*/?;

'''


#-------------------------------------------------------------------------------
## Asserts that string is a str. Raise an error otherwise
#
#  @param string input to be checked
#
#-------------------------------------------------------------------------------
def assertStr(string):
    assert isinstance(string, str), str(string) + " must be a string" 


#-------------------------------------------------------------------------------
## Asserts that listInst is a list. Raise an error otherwise
#
#  @param listInst input to be checked
#
#-------------------------------------------------------------------------------
def assertList(listInst):
    assert isinstance(listInst, list), str(listInst) + " must be a list" 


#-------------------------------------------------------------------------------
## Asserts that integer is a int. Raise an error otherwise
#
#  @param integer input to be checked
#
#-------------------------------------------------------------------------------
def assertInt(integer):
    assert isinstance(integer, int), str(integer) + " must be an integer" 


#-------------------------------------------------------------------------------
## Asserts that place is a Place. Raise an error otherwise
#
#  @param place input to be checked
#
#-------------------------------------------------------------------------------
def assertPlace(place):
    assert isinstance(place, Place), \
           "place must be an instance of the Place class" 


#-------------------------------------------------------------------------------
## Asserts that transition is a Transition. Raise an error otherwise
#
#  @param transition input to be checked
#
#-------------------------------------------------------------------------------
def assertTransition(transition):
    assert isinstance(transition, Transition), \
           "transition must be an instance of the Transition class" 


#-------------------------------------------------------------------------------
## Asserts that edge is a '-', '+' or '~'. Raise an error otherwise
#
#  @param edge input to be checked
#
#-------------------------------------------------------------------------------
def assertEdge(edge):
    assert edge in ['-', '+', '~'], "Unknown edge " + str(edge) 


#-------------------------------------------------------------------------------
## Transition Class
#
#-------------------------------------------------------------------------------
class Transition():

    #---------------------------------------------------------------------------
    ## Constructor
    #
    #  @param self pointer to self
    #
    #---------------------------------------------------------------------------
    def __init__(self):
        self.toPlaces = []
        self.fromPlaces = []

    #---------------------------------------------------------------------------
    ## Add place to the "to" list    
    #  
    #  @param self The object pointer.
    #  @param place Instance of the place class
    #
    #---------------------------------------------------------------------------
    def addTo(self, place):
        assertPlace(place)
        self.toPlaces.append(place)
    
    #---------------------------------------------------------------------------
    ## Add place to the "from" list    
    #  
    #  @param self The object pointer.
    #  @param place Instance of the place class
    #
    #---------------------------------------------------------------------------
    def addFrom(self, place):
        assertPlace(place)
        self.fromPlaces.append(place)   

    #---------------------------------------------------------------------------
    ## Return the "to" list    
    #  
    #  @param self The object pointer.
    #
    #---------------------------------------------------------------------------
    def getTo(self):
        return self.toPlaces

    #---------------------------------------------------------------------------
    ## Return the "from" list    
    #  
    #  @param self The object pointer.
    #
    #---------------------------------------------------------------------------
    def getFrom(self):
        return self.fromPlaces
        
    #---------------------------------------------------------------------------
    ## Is Enabled
    #  
    #  @param self The object pointer.
    #  @return boolean expression representing place enabled evaulation 
    #
    #---------------------------------------------------------------------------
    def isEnabled(self):
        ans = True
        for fromItem in self.getFrom():
            ans = ans & fromItem.hasToken()
        return ans    

    #---------------------------------------------------------------------------
    ## Remove one token from the place 
    #
    #  @param self pointer to self
    #  @return return a command that remove one token from the place
    #
    #---------------------------------------------------------------------------
    def incNextTokens(self):
        ans = CmdList()
        for toItem in self.getTo():
            ans.append(toItem.incNextToken())
        return ans    
        
        
    #---------------------------------------------------------------------------
    ## get all the tokens from the incomming places
    #  
    #  @param self The object pointer.
    #  @return a list of commands to remove one token from the incomming places  
    #
    #---------------------------------------------------------------------------
    def getTokens(self):
        ans = CmdList()
        for fromItem in self.getFrom():
            ans.append(fromItem.getToken())
        return ans    
        
    #---------------------------------------------------------------------------
    ## put all the tokens in the destination places
    #  
    #  @param self The object pointer.
    #  @return a list of commands to put one token into the destination places  
    #
    #---------------------------------------------------------------------------
    def putTokens(self):
        ans = CmdList()
        for toItem in self.getTo():
            ans.append(toItem.putToken())
        return ans   


#-------------------------------------------------------------------------------
## Place Class
#
#-------------------------------------------------------------------------------
class Place():
    
    #---------------------------------------------------------------------------
    ## Constructor
    #
    #  @param self pointer to self
    #  @param var variable that holds the ammount of tokens in the place
    #  @param name name of the place
    #  @param capacity capacity of the place
    #
    #---------------------------------------------------------------------------
    def __init__(self, var, inc, name, capacity = 1):
        assertInt(capacity)
        self.capacity = capacity
        self.toTransitions = []
        self.fromTransitions = []
        self.var = var
        self.inc = inc
        self.name = name
        
    #---------------------------------------------------------------------------
    ## Check if the place has tokens
    #
    #  @param self pointer to self
    #  @return return a boolean expression represening the presence of tokens
    #          in a place
    #
    #---------------------------------------------------------------------------
    def hasToken(self):
        return self.var > 0
        
    #---------------------------------------------------------------------------
    ## Remove one token from the place 
    #
    #  @param self pointer to self
    #  @return return a command that remove one token from the place
    #
    #---------------------------------------------------------------------------
    def getToken(self):
        return self.var.eq(self.var - 1)

    #---------------------------------------------------------------------------
    ## Remove one token from the place 
    #
    #  @param self pointer to self
    #  @return return a command that remove one token from the place
    #
    #---------------------------------------------------------------------------
    def incNextToken(self):
        return self.inc.eq(self.inc + 1)
        
        
    #---------------------------------------------------------------------------
    ## Put one token into the place 
    #
    #  @param self pointer to self
    #  @return return a command that put one token into the place
    #
    #---------------------------------------------------------------------------
    def putToken(self):
        return CmdList(
            self.var.eq(self.var + self.inc),
            self.inc.eq(0), 
            If(self.var > self.capacity)(
                Error(self.name + ' capacity was violated')
            )
        )
        
    #---------------------------------------------------------------------------
    ## Add transition to the "to" list    
    #  
    #  @param self The object pointer.
    #  @param transition Instance of the Transition class
    #
    #---------------------------------------------------------------------------
    def addTo(self, transition):
        assertTransition(transition)
        self.toTransitions.append(transition)
    
    #---------------------------------------------------------------------------
    ## Add transition to the "from" list    
    #  
    #  @param self The object pointer.
    #  @param transition Instance of the Transition class
    #
    #---------------------------------------------------------------------------
    def addFrom(self, transition):
        assertTransition(transition)
        self.fromTransitions.append(transition)

    #---------------------------------------------------------------------------
    ## Return the "to" list    
    #  
    #  @param self The object pointer.
    #  @return list of transitions that will be triggered
    #
    #---------------------------------------------------------------------------
    def getTo(self):
        return self.toTransitions

    #---------------------------------------------------------------------------
    ## Return the "from" list    
    #  
    #  @param self The object pointer.
    #  @return list of transitions that put a token in the place
    #
    #---------------------------------------------------------------------------
    def getFrom(self):
        return self.fromTransitions 


#-------------------------------------------------------------------------------
## Petri net class
#
#-------------------------------------------------------------------------------
class STG():

    #---------------------------------------------------------------------------
    ## Constructor
    #
    #  @param ast abstract syntax tree representing the petri net (parsed from 
    #      .g file by the grako with the grammar defined by GRAMMAR). However, 
    #      any list respecting the same format is also valid
    #
    #---------------------------------------------------------------------------
    def __init__(self, ast, sigMap = {"input"    : "input", 
                                      "output"   : "output",
                                      "internal" : "output"}):

        # Initialize local variables
        #-----------------------------------------------------------------------
        self.signals     = {}
        self.places      = {}
        self.transitions = {}
        self.markings    = {}
        self.capacity    = {}

        # verilogA module
        #-----------------------------------------------------------------------
        self.mod = HiLevelMod(ast["name"])
        self.gnd = self.mod.electrical("GND", direction = "inout")
        self.vdd = self.mod.electrical("VDD", direction = "inout")
        self.rf  = self.mod.par(1e-9, "RISE_FALL_PAR")
        self.dl  = self.mod.par(1e-9, "DELAY_PAR")
        self.inCap  = self.mod.par(10e-15, "IN_CAP_PAR")
        self.serRes = self.mod.par(100.00, "OUT_RES_PAR")
        self.rst = self.mod.dig(
                       domain = self.vdd, 
                       name = "RST", 
                       direction = "input", 
                       gnd = self.gnd,
                       inCap = self.inCap,
                   )
        self.rstAt = At( Above(0.05 + self.rst.diffHalfDomain) )()
        self.mod.analog(self.rstAt)
        self.done = self.mod.var(0)
        
        # Read all signals
        #-----------------------------------------------------------------------
        for sigType in ["input", "output", "internal"]:
            if sigType in ast:
                for signalList in ast[sigType]:
                    assertList(signalList)
                    for signal in signalList:
                        assertStr(signal)
                        assert not signal in self.signals, \
                               "Duplicated signal " + signal
                        par = 0
                        if sigType != "input":
                            par = self.mod.par(0, signal + "_RST_VALUE_PAR")
                        digpin = self.mod.dig(
                                     domain = self.vdd, 
                                     name = signal,
                                     value = par,
                                     direction = sigMap[sigType],
                                     delay = self.dl,
                                     rise = self.rf,
                                     fall = self.rf,
                                     gnd = self.gnd,
                                     inCap = self.inCap,
                                     serRes = self.serRes
                                 )
                        if sigMap[sigType] != "input":
                            self.rstAt.append(digpin.write(Bool(par)))
                        if sigMap[sigType] == "internal":
                            self.rstAt.append(digpin.lowZ())
                        self.signals[signal] = digpin     
                        self.transitions[signal] = {"+":{}, "-":{}, "~":{}}      
        assert len(self.signals) > 0, \
               " There is no input, output, internal signals. Odd.."

        # Read capacity
        #-----------------------------------------------------------------------
        if "capacity" in ast:
            for capList in ast["capacity"]:
                assertList(capList)
                for cap in capList:
                    assertList(cap)
                    assert len(cap) == 2, str(cap) + \
                           " capacity list must have two elements"
                    assertStr(cap[0])
                    assert not cap[0] in self.capacity.keys(), \
                           "Duplicated capacity for signal " + cap[0]
                    self.capacity[cap[0]] = int(cap[1]) 

        # Read markings
        #-----------------------------------------------------------------------
        if "marking" in ast:
            for markList in ast["marking"]:
                assertList(markList)
                for mark in markList:
                    assertList(mark)
                    assert len(mark) == 2 or len(mark) == 1, str(mark) + \
                           " marking list must have one or two elements"
                    assertStr(mark[0])
                    assert not mark[0] in self.markings.keys(), \
                           "Duplicated marking for signal " + mark[0]
                    if len(mark) < 2:
                        mark.append(1) 
                    self.markings[mark[0]] = int(mark[1]) 

        # Read Graph
        #-----------------------------------------------------------------------
        assert 'graph' in ast, "No graph declaration was found"
        arrows  = []
        for arrowList in ast["graph"]:
            assertList(arrowList)
            arrows = arrows + arrowList
        assert len(arrows) > 0, \
               " There is no arrows. Odd..."
        for arrow in arrows:
            assertList(arrow)
            #Read the left side of the arrow
            fromName = arrow[0]
            fromTP = self.matchTP(fromName)
            #Read the remaining elements of the list
            for toName in arrow[1:]:
                toTP = self.matchTP(toName)   
                assert not (isinstance(toTP, Place) and \
                            isinstance(fromTP, Place)), \
                       "There can't be arrow from place " + fromTPName +\
                       " to place " + toTPName
                #Check if there is an implicit place
                if isinstance(toTP, Transition) and \
                   isinstance(fromTP, Transition):
                   impName = fromName + "," + toName
                   impPlace = self.matchPlace(impName)
                   fromTP.addTo(impPlace)
                   toTP.addFrom(impPlace)
                   impPlace.addFrom(fromTP)
                   impPlace.addTo(toTP)
                #A pair of transition place otherwise
                else:
                   fromTP.addTo(toTP)
                   toTP.addFrom(fromTP)
                  
        # build stg
        #-----------------------------------------------------------------------   
        cmdOut = CmdList()                     
        for signal in self.signals:
            signalObj = self.signals[signal]
            
            # Process signals
            #-------------------------------------------------------------------
            sigIfRising  = If(self.rst.read())(
                               self.done.eq(0)
                           )
            sigIfFalling = If(self.rst.read())(
                               self.done.eq(0)
                           )
            self.mod.analog(
                At(Cross(signalObj.diffHalfDomain, "rising"))(
                    sigIfRising
                ),
                At(Cross(signalObj.diffHalfDomain, "falling"))(
                    sigIfFalling
                )
            )   

            if not isinstance(signalObj, hilevelmod.DigIn): 
                for edge in ['+', '-', '~']:  
                    for transition in self.transitions[signal][edge].keys():     
                        transitionObj = self.transitions[signal][edge][transition]
                        if edge == '+':
                            sigIfRising.append(True,
                                transitionObj.putTokens(),    
                            )
                            cmdOut.append(
                                If(transitionObj.isEnabled())( 
                                    transitionObj.getTokens(),
                                    transitionObj.incNextTokens(),
                                    signalObj.write(True) 
                                )  
                            )
                        elif edge == '-':
                            sigIfFalling.append(True,
                                transitionObj.putTokens(),    
                            )
                            cmdOut.append(
                                If(transitionObj.isEnabled())( 
                                    transitionObj.getTokens(),
                                    transitionObj.incNextTokens(),
                                    signalObj.write(False) 
                                )  
                            )
                        else:
                            sigIfRising.append(True,
                                transitionObj.putTokens(),    
                            )
                            sigIfFalling.append(True,
                                transitionObj.putTokens(),    
                            )
                            cmdOut.append(
                                If(transitionObj.isEnabled())( 
                                    transitionObj.getTokens(),
                                    transitionObj.incNextTokens(),
                                    signalObj.toggle(False) 
                                )  
                            )
            else:
                for edge in ['+', '-', '~']:  
                    for transition in self.transitions[signal][edge].keys():    
                        transitionObj = self.transitions[signal][edge][transition] 
                        if edge in ['+', '~']:
                            sigIfRising.append(True,
                                If(transitionObj.isEnabled())(
                                    transitionObj.getTokens(),
                                    transitionObj.incNextTokens(),
                                    transitionObj.putTokens(), 
                                    self.done.eq(1)       
                                ),
                            )  
                        if edge in ['-', '~']:
                            sigIfFalling.append(True,
                                If(transitionObj.isEnabled())(
                                    transitionObj.getTokens(),
                                    transitionObj.incNextTokens(),
                                    transitionObj.putTokens(), 
                                    self.done.eq(1)       
                                ),
                            )  
                sigIfRising.append(True,
                    If(self.done == 0)(
                        Error("No transition related to " + \
                              signal + \
                              "+ is enabled")  
                    )  
                )
                sigIfFalling.append(True,
                    If(self.done == 0)(
                        Error("No transition related to " + \
                              signal + \
                              "- is enabled")  
                    )  
                )
        self.mod.analog(
            If(self.rst.read())(
                self.done.eq(0),  #dummy for no outputs     
                cmdOut
            )
        )
                        
    #---------------------------------------------------------------------------
    ## match a place with an specific name   
    #  
    #  @param self The object pointer.
    #  @return the place
    #
    #---------------------------------------------------------------------------                
    def matchPlace(self, name):
        if name in self.places:
            P = self.places[name]
        else:
            marking  = 0
            capacity = 1
            if name in self.markings.keys():
                marking = self.markings[name]
            if name in self.capacity.keys():
                capacity = self.capacity[name]
            var = self.mod.var(marking)
            inc = self.mod.var(0)
            self.rstAt.append(var.eq(marking))
            P = Place(var,
                      inc,
                      name,
                      capacity)
            self.places[name] = P 
        return P 
        
    #---------------------------------------------------------------------------
    ## match a place or a transition with an specific name   
    #  
    #  @param self The object pointer.
    #  @return the place or the transition
    #
    #--------------------------------------------------------------------------- 
    def matchTP(self, name):
        pattern = '([a-zA-Z_][a-zA-Z_0-9.]*)([+-~]?)(/[0-9]*)?'
        m = re.findall(pattern, name)
        if len(m) != 0:
            signame = m[0][0]
            sigEdge = m[0][1]
            if signame in self.signals:
                if name in self.transitions[signame][sigEdge]:
                    TP = self.transitions[signame][sigEdge][name]
                else:
                    TP = Transition()
                    self.transitions[signame][sigEdge][name] = TP 
            else:
                TP = self.matchPlace(name)
        else:
            raise Error("Something went wrong")
        return TP
        
    #---------------------------------------------------------------------------
    ## return the verilogA  
    #  
    #  @param self The object pointer.
    #  @return the verilogA string
    #
    #---------------------------------------------------------------------------                    
    def getVA(self):
        return self.mod.getVA()


#-------------------------------------------------------------------------------
## Main
#
#-------------------------------------------------------------------------------
if __name__ == "__main__":

    #---------------------------------------------------------------------------
    # Input arguments
    #---------------------------------------------------------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'stg', 
        metavar='stg', 
        type=str, 
        nargs=1,
        help='.g file containing the description of the stg'
    )
    parser.add_argument(
        '-o', 
        action='store',
        dest='outFile',
        default='verilogA.va',
        help='output file name'
    )
    parser.add_argument(
        '-seeInternals', 
        action='store_true',
        default=False,
        dest='seeInt',
        help='Internal signals will be converted into in/out ports.'
    ) 
    parser.add_argument(
        '-allInputs', 
        action='store_true',
        default=False,
        dest='allInp',
        help='Convert all signals into inputs. If seeInternals is enabled, ' +\
             'internal signals will also be converted to inputs.'
    )     
    results = parser.parse_args()

    #---------------------------------------------------------------------------
    # Open stg file
    #---------------------------------------------------------------------------
    try:
        #Open stg file
        with open(results.stg[0]) as content_file:
            content = content_file.read()
        #Create stg
        ast = parse(GRAMMAR, content)
        mapping = {"input"    : "input", 
                   "output"   : "output",
                   "internal" : "internal"}
                            
        if results.seeInt and (not results.allInp):
            mapping["internal"] = "output"
        elif results.seeInt and results.allInp:
            mapping["internal"] = "input"
        if results.allInp:
            mapping["output"] = "input"

        stg = STG(ast, mapping)
        
        #Open log file
        f = open(results.outFile, "w")
        f.write(stg.getVA())
        f.close()
    except Exception as e:
        raise e
        print("Error: " + str(e))
        exit(-1)

    #---------------------------------------------------------------------------
    # Success
    #---------------------------------------------------------------------------
    exit(0)
