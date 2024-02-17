Have the espresso-vgen.sh, vgen.py, and veriloggatetree.py files
in the same directory as the espresso.linux executable.
Make vgen.py executable with chmod +x vgen.py, and be sure that you
have python3 installed in your bin directory.

Run ./espresso-vgen.sh input output, where:
    input is a valid espresso input, i.e., truth table
    output is some file that the verilog will be written to

FOR COMBINATIONAL CIRCUITS:
    Run the command normally, the only restriction is that output
    names cannot begin with "next".

FOR STATE MACHINES:
    Structure the state bits to be something for the form X and
    nextX such that X is some bit describing the state and nextX
    is that same bit for the next clock cycle.
    The program will auto-generate the clk, r, and s inputs for the
    D-FlipFlops.

For both types the command is the same, the program differentiates
the two types via the naming convention of the inputs/outputs. As a 
result, the program can handle circuits with both combinational and
sequential elements.
