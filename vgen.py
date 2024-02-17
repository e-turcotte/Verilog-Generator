#!/bin/python3

import sys
import re
import veriloggatetree

LINELEN = 75

def main():
    print(''.center(LINELEN, "-"))
    print('[ PARSING ESPRESSO OUTPUT ]'.center(LINELEN, "="))
    print(''.center(LINELEN, "-"), "\n")
    inputs, outputs, products = parseInputFile()
    
    print('\n'.ljust(LINELEN+1, "-"))
    print('[ MAPPING TO GATES ]'.center(LINELEN, "="))
    print(''.center(LINELEN, "-"), "\n")
    genwiredict, genpartlist = mapGates(inputs, outputs, products)

    print('\n'.ljust(LINELEN+1, "-"))
    print('[ OPTIMIZING COMBINATIONAL PATHING ]'.center(LINELEN, "="))
    print(''.center(LINELEN, "-"), "\n")
    optwiredict, optpartlist = reduceGateTree(inputs, outputs, genwiredict, genpartlist)

    print('\n'.ljust(LINELEN+1, "-"))
    print('[ TRANSLATING TO VERILOG ]'.center(LINELEN, "="))
    print(''.center(LINELEN, "-"), "\n")
    writeVerilog(inputs, outputs, optwiredict, optpartlist)


def writeVerilog(inputs, outputs, wiredict, partlist):
    statemachine = {}
    sequential = False
    for o in outputs:
        if o[:4] == "next" and o[4:] in inputs:
            statemachine[o[4:]] = [wiredict.pop(o[4:]), wiredict.pop(o)]
            sequential = True
    statemachinestring = "\twire "
    for state in statemachine.keys():
        statemachinestring = statemachinestring + state + ", next" + state + ", "
        inputs.remove(state)
        outputs.remove("next"+state)
    statemachinestring = statemachinestring[:len(statemachinestring)-2] + ";\n\n"

    f = open(sys.argv[1], "w")
    module_name = sys.argv[2]
    print("Creating " + module_name + " Module...\n")

    inputstring = wiredict[inputs[0]].signal
    for j in range(1, len(inputs)):
        inputstring = inputstring + ", " + inputs[j]
    outputstring = wiredict[outputs[0]].signal
    for j in range(1, len(outputs)):
        outputstring = outputstring + ", " + outputs[j]
    f.write("module " + module_name + "(input " + inputstring + ",\n")
    if sequential:
        f.write("".ljust(len("module " + module_name + "("), " ") + "input clk, r, s,\n")
    f.write("".ljust(len("module " + module_name + "("), " ") + "output " + outputstring + ");\n\n")
    for i in inputs:
        del wiredict[i]
    for o in outputs:
        del wiredict[o]

    f.write("\t" + veriloggatetree.Wire.toVerilog(list(wiredict.values())) + "\n" + (statemachinestring if sequential else "\n"))
    for j in range(len(partlist)):
        f.write("\t" + partlist[j].toVerilog("g"+str(j)) + "\n")
    f.write("\n")
    for w in wiredict.values():
        if w.signal in outputs or w.signal[4:] in statemachine.keys():
            f.write("\tassign " + w.signal + " = " + w.name + ";\n")
    f.write("\n")
    for s in statemachine.keys():
        f.write("\tdff$ " + s + "dff(.clk(clk), .d(next" + s + "), .q(" + s + "), .qbar(), .r(r), .s(s));\n")
    f.write("\nendmodule")

    f.close()


def reduceGateTree(inputs, outputs, genwiredict, genpartlist):
    startdelay = veriloggatetree.calcCriticalPathDelay([genwiredict[i] for i in inputs], [genwiredict[o] for o in outputs])
    print("Staring Critical Delay:", str(startdelay)+"ns\n")

    optwiredict = genwiredict.copy()
    optpartlist = genpartlist.copy()

    def alternateCascadeGates(wire):
        print("do thang")
        
    
    alternateCascadeGates(None)

    wirestoremove = []
    for key in optwiredict.keys():
        if optwiredict[key].signal in outputs and not key in outputs and not optwiredict[key].driving:
            wirestoremove.append(key)
    for w in wirestoremove:
        del optwiredict[w]

    enddelay = veriloggatetree.calcCriticalPathDelay([optwiredict[i] for i in inputs], [optwiredict[o] for o in outputs])
    print("Ending Critical Delay:", str(enddelay)+"ns")
    print("Time Saved:", str(startdelay-enddelay)+"ns")
    return optwiredict, optpartlist

def mapGates(inputs, outputs, products):
    line_len_prods = len(max([str(p) for p in products], key = len))+5
    wiredict = {}
    partlist = []
    for i in inputs:
        wiredict[i] = veriloggatetree.Wire(i)

    for p in products:
        termtobuild = p[0].copy()
        p.append([])
        for i in p[0]:
            if i[0] == '~' and not i in wiredict:
                w = veriloggatetree.Wire("floating")
                partlist.append(veriloggatetree.Inv(wiredict[i[1:]], w))
                wiredict[i] = w
        while termtobuild:
            num_inputs = 1
            if len(termtobuild) % 4 == 0:
                num_inputs = 4
            elif len(termtobuild) % 3 == 0 or (len(termtobuild) % 2 == 1 and len(termtobuild) != 1):
                num_inputs = 3
            elif len(termtobuild) % 2 == 0:
                num_inputs = 2
            gateinputsignals = ""
            for terminput in termtobuild[:num_inputs]:
                gateinputsignals = gateinputsignals + terminput
            if num_inputs != 1:
                if not "&("+gateinputsignals+")" in wiredict:
                    w = veriloggatetree.Wire("floating")
                    partlist.append(veriloggatetree.And([wiredict[key] for key in termtobuild[:num_inputs]], num_inputs, w))
                    wiredict["&("+gateinputsignals+")"] = w
                for j in reversed(range(num_inputs)):
                    termtobuild.remove(termtobuild[j])
                if termtobuild:
                    termtobuild.append("&("+gateinputsignals+")")
                else:
                    print((str(p[:2])).ljust(line_len_prods, ' '), "-->", p[1], "|=", "&("+gateinputsignals+")")
                    p[2] = "&("+gateinputsignals+")"
            else:
                print((str(p[:2])).ljust(line_len_prods, ' '), "-->", p[1], "|=", gateinputsignals)
                p[2] = termtobuild[0]
                termtobuild.remove(termtobuild[0])
    
    print()
    for o in outputs:
        termlist = []
        for p in products:
            if o in p[1]:
                termlist.append(p[2]) 
        while termlist:
            num_inputs = 1
            if len(termlist) % 4 == 0:
                num_inputs = 4
            elif len(termlist) % 3 == 0 or (len(termlist) % 2 == 1 and len(termlist) != 1):
                num_inputs = 3
            elif len(termlist) % 2 == 0:
                num_inputs = 2
            if num_inputs != 1:
                gateinputsignals = ""
                for terminput in termlist[:num_inputs]:
                    gateinputsignals = gateinputsignals + terminput
                if not "|("+gateinputsignals+")" in wiredict:
                    w = veriloggatetree.Wire("floating")
                    partlist.append(veriloggatetree.Or([wiredict[key] for key in termlist[:num_inputs]], num_inputs, w))
                    wiredict["|("+gateinputsignals+")"] = w
                for j in reversed(range(num_inputs)):
                    termlist.remove(termlist[j])
                if termlist:
                    termlist.append("|("+gateinputsignals+")")
                else:
                    wiredict[o] = w
                    wiredict[o].signal = o
            else:
                wiredict[o] = wiredict[termlist[0]]
                wiredict[o].signal = o
                termlist.remove(termlist[0])
            
    line_len_wires = len(max([str(w) for w in wiredict], key = len))+5
    for key, value in wiredict.items():
        print(key.ljust(line_len_wires, ' '), ":", value)
    print()
    for part in partlist:
        print(part)
    
    return wiredict, partlist



def parseInputFile():
    ttfile = sys.stdin.read().split("\n")
    line_len = len(max(ttfile, key = len))+5

    assert re.search(".i [0-9]+", ttfile[0])
    num_inputs = int(re.findall("[0-9]+", ttfile[0])[0])
    print(ttfile[0].ljust(line_len, ' '), ": # of Inputs <=", num_inputs)
    assert re.search(".o [0-9]+", ttfile[1])
    num_outputs = int(re.findall("[0-9]+", ttfile[1])[0])
    print(ttfile[1].ljust(line_len, ' '), ": # of Outputs <=", num_outputs)
    assert re.search(".ilb ([A-Za-z0-9]+ ?){"+str(num_inputs)+"}", ttfile[2])
    inputs = ttfile[2].split(" ")[1:]
    print(ttfile[2].ljust(line_len, ' '), ": Inputs <=", inputs)
    assert re.search(".ob ([A-Za-z0-9\[\]]+ ?){"+str(num_outputs)+"}", ttfile[3])
    outputs = ttfile[3].split(" ")[1:]
    print(ttfile[3].ljust(line_len, ' '), ": Outputs <=", outputs)
    assert re.search(".p [0-9]+", ttfile[4])
    num_products = int(re.findall("[0-9]+", ttfile[4])[0])
    print(ttfile[4].ljust(line_len, ' '), ": # of Products <=", num_products, "\n")

    products = []
    for line in ttfile[5:5+num_products]:
        prodinp = []
        prodoutp = []
        assert re.search("[01-]{"+str(num_inputs)+"} [01]{"+str(num_outputs)+"}", line)
        for i in range(num_inputs):
            if line[i] != '-':
                prodinp.append(inputs[i] if line[i] == '1' else str("~")+inputs[i])
        for o in range(num_outputs):
            if line[o+num_inputs+1] == '1':
                prodoutp.append(outputs[o])
        print(line.ljust(line_len, ' '), ":", prodoutp, "|=", prodinp)
        products.append([prodinp, prodoutp])
    
    assert re.search(".e", ttfile[5+num_products])
    print(("\n" + ttfile[5+num_products]).ljust(line_len+1, ' '), ": EOF")

    return inputs, outputs, products



if __name__ == "__main__":
    main()
