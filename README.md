# stg2veriloga

Mixed signal IPs often require some sort of asynchronous logic. This logic can be modeled by means of Signal Transition Graphs (STG) with the [workcraft](https://workcraft.org/) tool. The purpose of stg2veriloga is to convert a non-synthesizable STG into a veriloga model in order to aid the specification and initial validation of analog IPs that depend on asynchronous logic. 

# Dependencies 

You will need to install [workcraft](https://workcraft.org/) and all the stg2veriloga dependencies.
The dependencies can be installed by typing the following command on a terminal:

```
    pip3 install -r requirements.txt
```

You can confirm that everything is working correctly by typing:

```
    python3 stg2veriloga/stg2veriloga.py  -h 
```

or:

```
    python3 stg2veriloga/stg2veriloga.py  example/STG.g
```

# Example

- After everything is set up, you can draw, as an example, the following STG using [workcraft](https://workcraft.org/):

![plot](./example/stg.png)

- stg2veriloga relies on the assumptions of "consistency" and "deadlock freeness", but it doesn't check these properties. Therefore, you must run these checks using [workcraft](https://workcraft.org/). The STG must also be deterministic, so you don't get wrong results.

- Once the STG is finished and passes the checks, you can export the STG to a .g file by clicking on "file" -> "Export" -> "Signal Transition Graph (*.g)". The result of these steps will be a file similar to the one provided in the example folder ([STG.g](./example/STG.g)).

- You can now convert the .g file to a veriloga model:

```
    python3 stg2veriloga/stg2veriloga.py  example/STG.g
```

- stg2veriloga isn't capable of inferring the initial states of the outputs. Therefore, you need to set them manually through the parameters provided in the verilogA. You can also set the input capacitance, output resistance, rise time, fall time, and delay (the interval between a output transition becoming enabled and the output rise/fall edge) through the parameters. If the initial output states are wrong, the simulation will eventually throw a fatal error and stop.

![plot](./example/param.png)


- The simulation result of this example is shown below:

![plot](./test/wave.png)

# Errors 

stg2veriloga generates veriloga code to throw a fatal error during simulation whenever some inconsistency is detected. Check the simulation log to see what went wrong. 

# Extra options

Options to convert all signals to inputs, make the internal signals observable, and change some default names are available. You can check these options by typing:

```
    python3 stg2veriloga/stg2veriloga.py  -h 
```

# Setup tools

If you which to install the program in your computer, you can use setup tools to install it. Go one directory above this one and type:


```
    pip3 install stg2veriloga/
```

Now you should have the command stg2veriloga available in your terminal.















