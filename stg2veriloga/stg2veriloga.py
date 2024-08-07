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
from vagen import If, While, Bool, HiLevelMod, At, Fatal, Branch, \
                  Above, Cross, CmdList, Strobe, hilevelmod
from tatsu import compile


#-------------------------------------------------------------------------------
## Parser Grammar
#
#-------------------------------------------------------------------------------
GRAMMAR = '''


    @@grammar::Calc

    @@whitespace::/[\t ]+/

    @@eol_comments :: /#[^\n]*\n/

    start   = stg $ ;

    stg     = {'\\n'}* '.model' name:name {'\\n'}+ 
              {input+:inputs        |  
               output+:outputs      | 
               internal+:internals  | 
               dummy+:dummy         |
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
     
    name      = /[a-zA-Z_][a-zA-Z_0-9]*/;

    value     = /[0-9]+/;

    tranPlace = ?/[a-zA-Z_][a-zA-Z_0-9\+\-\~/]*/?;

    tranPlaceComma = ?/[a-zA-Z_][a-zA-Z_0-9\+\-\~/]*,[a-zA-Z_][a-zA-Z_0-9\+\-\~/]*/?;

'''


#-------------------------------------------------------------------------------
## Asserts that string is a str. Raise an error otherwise
#
#  @param string input to be checked
#
#-------------------------------------------------------------------------------
def assertStr(string):
    assert isinstance(string, str), f"{string} must be a string" 


#-------------------------------------------------------------------------------
## Asserts that listInst is a list. Raise an error otherwise
#
#  @param listInst input to be checked
#
#-------------------------------------------------------------------------------
def assertList(listInst):
    assert isinstance(listInst, list), f"{listInst} must be a list" 


#-------------------------------------------------------------------------------
## Asserts that integer is a int. Raise an error otherwise
#
#  @param integer input to be checked
#
#-------------------------------------------------------------------------------
def assertInt(integer):
    assert isinstance(integer, int), f"{integer} must be an integer" 


#-------------------------------------------------------------------------------
## Asserts that place is a Place. Raise an error otherwise
#
#  @param place input to be checked
#
#-------------------------------------------------------------------------------
def assertPlace(place):
    assert isinstance(place, Place), \
           f"{place} must be an instance of the Place class" 


#-------------------------------------------------------------------------------
## Asserts that transition is a Transition. Raise an error otherwise
#
#  @param transition input to be checked
#
#-------------------------------------------------------------------------------
def assertTransition(transition):
    assert isinstance(transition, Transition), \
           f"{transition} must be an instance of the Transition class" 


#-------------------------------------------------------------------------------
## Asserts that edge is a '-', '+' or '~'. Raise an error otherwise
#
#  @param edge input to be checked
#
#-------------------------------------------------------------------------------
def assertEdge(edge):
    assert edge in ['-', '+', '~'], f"Unknown edge {edge}" 


#-------------------------------------------------------------------------------
## Transition Class
#
#-------------------------------------------------------------------------------
class Transition():

    #---------------------------------------------------------------------------
    ## Constructor
    #
    #  @param self pointer to self
    #  @param var variable representing a ongoing transition
    #
    #---------------------------------------------------------------------------
    def __init__(self, var):
        self.toPlaces = []
        self.fromPlaces = []
        self.var = var

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
    #  @return boolean expression representing place enabled evaluation 
    #
    #---------------------------------------------------------------------------
    def isEnabled(self):
        ans = True
        for fromItem in self.getFrom():
            ans = ans & fromItem.hasToken()
        return ans    
        
    #---------------------------------------------------------------------------
    ## Is On going
    #  
    #  @param self The object pointer.
    #  @return boolean expression representing an evaluation if the transition
    #          is on going
    #
    #---------------------------------------------------------------------------
    def isOnGoing(self):
        return self.var
        
    #---------------------------------------------------------------------------
    ## get all the tokens from the incomming places
    #  
    #  @param self The object pointer.
    #  @return a list of commands to remove one token from the incomming places  
    #
    #---------------------------------------------------------------------------
    def getTokens(self):
        ans = CmdList(self.var.eq(True))
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
        ans = CmdList(self.var.eq(False))
        for toItem in self.getTo():
            ans.append(toItem.putToken())
        return ans   
        
    #---------------------------------------------------------------------------
    ## Fire up the transition imediatelly
    #  
    #  @param self The object pointer.
    #  @return a list of commands to fire the transition  
    #
    #---------------------------------------------------------------------------
    def fire(self):
        ans = CmdList()
        for fromItem in self.getFrom():
            ans.append(fromItem.getToken())
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
    def __init__(self, var, errVar, name, capacity = 1):
        assertInt(capacity)
        self.capacity = capacity
        self.toTransitions = []
        self.fromTransitions = []
        self.var = var
        self.name = name
        self.errVar = errVar
        
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
    ## Put one token into the place 
    #
    #  @param self pointer to self
    #  @return return a command that put one token into the place
    #
    #---------------------------------------------------------------------------
    def putToken(self):
        return CmdList(
            self.var.eq(self.var + 1),
            If(self.var > self.capacity)(
                Strobe(f'{self.name} capacity was violated'),
                self.errVar.eq(True)
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
    #      .g file by the tatsu with the grammar defined by GRAMMAR). However, 
    #      any list respecting the same format is also valid
    #
    #---------------------------------------------------------------------------
    def __init__(self, 
                 ast, 
                 sigMap,
                 vddName, 
                 vssName,
                 rstName,
                 seeError): 

        # Initialize local variables
        #-----------------------------------------------------------------------
        self.signals     = {}
        self.places      = {}
        self.transitions = {}
        self.markings    = {}
        self.capacity    = {}
        self.dummies     = []
        sigMap['dummy'] = 'dummy'
        
        # verilogA module
        #-----------------------------------------------------------------------
        self.mod = HiLevelMod(ast["name"])
        self.gnd = self.mod.electrical(vssName, direction = "inout")
        self.vdd = self.mod.electrical(vddName, direction = "inout")
        self.rf  = self.mod.par(100e-12, "RISE_FALL_PAR")
        self.dl  = self.mod.par(100e-12, "DELAY_PAR")
        self.inCap  = self.mod.par(10e-15, "IN_CAP_PAR")
        self.serRes = self.mod.par(10e3, "OUT_RES_PAR")
        self.errVar = self.mod.var(name = "STG_ERROR", value = False)
        self.rst = self.mod.dig(
                       domain = self.vdd, 
                       name = rstName, 
                       direction = "input", 
                       gnd = self.gnd,
                       inCap = self.inCap,
                   )
        self.rstAt = CmdList()
        self.mod.analog(
            At( Cross(self.rst.diffHalfDomain, "both") )(),
            If( ~self.rst.read() )(
                self.rstAt
            )
        )
        self.done = self.mod.var(value = 0, name = "_$done")
        self.iter = self.mod.var(value = 0, name = "_$counter")

        if seeError:
            self.errorPin = self.mod.dig(
                domain = self.vdd, 
                name = "__STG_ERROR__",
                value = False,
                direction = 'output',
                delay = 0,
                rise = 1e-12,
                fall = 1e-12,
                gnd = self.gnd
            )
       
        # Read all signals
        #-----------------------------------------------------------------------
        for sigType in ["output", "input", "internal", "dummy"]:
            if sigType in ast:
                for signalList in ast[sigType]:
                    assertList(signalList)
                    for signal in signalList:
                        assertStr(signal)
                        if sigMap[sigType] == "input" or \
                           sigMap[sigType] == "output":
                            assert not signal in self.signals, \
                                   f"Duplicated signal {signal}"
                            par = 0
                            if sigMap[sigType] == "output":
                                par = self.mod.par(0, f"{signal}_RST_VALUE_PAR")
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
                            if sigMap[sigType] == "output":
                                self.rstAt.append(digpin.write(Bool(par)))
                            self.signals[signal] = digpin     
                            self.transitions[signal] = {"+":{}, "-":{}, "~":{}}
                        else:
                            self.dummies.append(signal)
                            self.transitions[signal] = {}     
                                             
                    
        # Assert presence of inputs and outputs.
        #-----------------------------------------------------------------------                                   
        assert len(self.signals) > 0, \
               " There is no input or output signals. Odd.."

        # Read capacity
        #-----------------------------------------------------------------------
        if "capacity" in ast:
            for capList in ast["capacity"]:
                assertList(capList)
                for cap in capList:
                    cap = list(cap)
                    assert len(cap) == 2, \
                           f"{cap} capacity list must have two elements"
                    assertStr(cap[0])
                    assert not cap[0] in self.capacity.keys(), \
                           f"Duplicated capacity for signal {cap[0]}"
                    self.capacity[cap[0]] = int(cap[1]) 

        # Read markings
        #-----------------------------------------------------------------------
        if "marking" in ast:
            for markList in ast["marking"]:
                assertList(markList)
                for mark in markList:
                    mark = list(mark)
                    assert len(mark) == 2 or len(mark) == 1, \
                           f"{mark} marking list must have one or two elements"
                    assertStr(mark[0])
                    assert not mark[0] in self.markings.keys(), \
                           f"Duplicated marking for signal {mark[0]}"
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
                     (f"There can't be arrow from place {fromTPName} to place "
                      f"{toTPName}")
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
        for dummy in self.dummies:
            for transition in self.transitions[dummy]:
                transitionObj = self.transitions[dummy][transition]
                cmdOut.append(
                    If(transitionObj.isEnabled())( 
                        transitionObj.fire(),
                        self.done.eq(0)
                    )  
                )                    
                             
        for signal in self.signals:
            signalObj = self.signals[signal]
            
            # Process signals
            #-------------------------------------------------------------------
            sigIfRising  = If(self.rst.read() & 
                              (Branch(self.vdd, self.gnd).v > 0.05))(
                               self.done.eq(0)
                           )
            sigIfFalling = If(self.rst.read() & 
                              (Branch(self.vdd, self.gnd).v > 0.05))(
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
                                If(transitionObj.isOnGoing())(
                                    transitionObj.putTokens(), 
                                    self.done.inc()       
                                ),
                            )  
                            cmdOut.append(
                                If(transitionObj.isEnabled())( 
                                    transitionObj.getTokens(),
                                    If(signalObj.getST())(
                                        Strobe( (f"{transition} failed to trigger "
                                                 f"because {signal} is already "
                                                  "high") ),
                                        self.errVar.eq(True)
                                    ).Else(
                                        signalObj.write(True)
                                    ),
                                    self.done.eq(0)
                                )  
                            )
                        elif edge == '-':
                            sigIfFalling.append(True,
                                If(transitionObj.isOnGoing())(
                                    transitionObj.putTokens(), 
                                    self.done.inc()       
                                ),
                            ) 
                            cmdOut.append(
                                If(transitionObj.isEnabled())( 
                                    transitionObj.getTokens(),
                                    If(signalObj.getST())(
                                        signalObj.write(False)
                                    ).Else(
                                        Strobe( (f"{transition} failed to trigger "
                                                 f"because {signal} is already "
                                                  "low") ),
                                        self.errVar.eq(True)
                                    ),
                                    self.done.eq(0) 
                                )  
                            )
                        else:
                            sigIfRising.append(True,
                                If(transitionObj.isOnGoing())(
                                    transitionObj.putTokens(), 
                                    self.done.inc()       
                                ),
                            ) 
                            sigIfFalling.append(True,
                                If(transitionObj.isOnGoing())(
                                    transitionObj.putTokens(), 
                                    self.done.inc()       
                                ),
                            ) 
                            cmdOut.append(
                                If(transitionObj.isEnabled())( 
                                    transitionObj.getTokens(),
                                    signalObj.toggle(),
                                    self.done.eq(0) 
                                )  
                            )
            else:
                for edge in ['+', '-', '~']:  
                    for transition in self.transitions[signal][edge].keys():    
                        transitionObj = self.transitions[signal][edge][transition] 
                        if edge in ['+', '~']:
                            sigIfRising.append(True,
                                If(transitionObj.isEnabled())(
                                    transitionObj.fire(), 
                                    self.done.inc()       
                                ),
                            )  
                        if edge in ['-', '~']:
                            sigIfFalling.append(True,
                                If(transitionObj.isEnabled())(
                                    transitionObj.fire(),
                                    self.done.inc()       
                                ),
                            )  
            sigIfRising.append(True,
                If(self.done == 0)(
                    Strobe(f"No transitions related to {signal}+ are enabled"),
                    self.errVar.eq(True)
                ),  
                If(self.done > 1)(
                    Strobe(f"More than one transition fires for {signal}+"),
                    self.errVar.eq(True)
                )  
            )
            sigIfFalling.append(True,
                If(self.done == 0)(
                    Strobe(f"No transitions related to {signal}- are enabled"),
                    self.errVar.eq(True)
                ),
                If(self.done > 1)(
                    Strobe(f"More than one transition fires for {signal}-"),
                    self.errVar.eq(True)
                )  
            )
        
        if len(cmdOut) > 0: 
            self.mod.analog(
                If(self.rst.read() & 
                   (Branch(self.vdd, self.gnd).v > 0.05))(
                    self.done.eq(0),
                    self.iter.eq(0),
                    While(~Bool(self.done))(
                        self.iter.inc(),
                        self.done.eq(1),
                        cmdOut,
                        If(self.iter > 500)(
                            Fatal(("STG seems to be stuck in a infinite loop "
                                   "of dummy, internal or output transitions.")) 
                        )
                    )
                )
            )
        if seeError:
            self.mod.analog(self.errorPin.write(self.errVar))
                       
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
            var = self.mod.var(value = marking, 
                               name = f"P_{name}".replace(",", "$$").\
                                                  replace("+", "$p").\
                                                  replace("-", "$m").\
                                                  replace("/", "$"))
            self.rstAt.append(var.eq(marking))
            P = Place(var,
                      self.errVar,
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
                    if not isinstance(self.signals[signame], hilevelmod.DigIn):
                        var = self.mod.var(value = False,
                                           name = f"T_{name}".replace("/", "$").\
                                                              replace("+", "$p").\
                                                              replace("-", "$m"))
                        self.rstAt.append(var.eq(False))
                        TP = Transition(var)
                    else:
                        TP = Transition(None)
                    self.transitions[signame][sigEdge][name] = TP 
            elif signame in self.dummies:
                if name in self.transitions[signame]:
                    TP = self.transitions[signame][name]
                else:
                    TP = Transition(None)
                    self.transitions[signame][name] = TP
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
## cli
#
#-------------------------------------------------------------------------------
def cli():

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
        '-vdd', 
        action='store',
        dest='vdd',
        default='VDD',
        help='VDD name'
    )
    parser.add_argument(
        '-vss', 
        action='store',
        dest='vss',
        default='VSS',
        help='VSS name'
    )
    parser.add_argument(
        '-rst', 
        action='store',
        dest='rst',
        default='RST',
        help='RST name'
    )
    parser.add_argument(
        '-seeInternals', 
        action='store_true',
        default=False,
        dest='seeInt',
        help='Internal signals will be converted into in/out ports.'
    ) 
    parser.add_argument(
        '-seeError', 
        action='store_true',
        default=False,
        dest='seeError',
        help='See error signal.'
    ) 
    parser.add_argument(
        '-allInputs', 
        action='store_true',
        default=False,
        dest='allInp',
        help=('Convert all signals into inputs. If seeInternals is enabled, '
              'internal signals will also be converted to inputs.')
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
        model = compile(GRAMMAR)
        ast = model.parse(content)
        mapping = {"input"    : "input", 
                   "output"   : "output",
                   "internal" : "internal"}
                            
        if results.seeInt and (not results.allInp):
            mapping["internal"] = "output"
        elif results.seeInt and results.allInp:
            mapping["internal"] = "input"
        if results.allInp:
            mapping["output"] = "input"

        stg = STG(ast, mapping, results.vdd, results.vss, results.rst, results.seeError)
        
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


#-------------------------------------------------------------------------------
## main
#
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    cli()

