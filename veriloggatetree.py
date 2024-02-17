class Gate:
    def __init__(self, inputs, num_inputs, output, delay):
        self.inputs = inputs.copy()
        self.num_inputs = num_inputs
        self.output = output
        self.delay = delay

    def __repr__(self):
        return self.__class__.__name__ + str(self.num_inputs) + "(" + self.output.signal + " <= " + str([i.signal for i in self.inputs]) +  ")"
        #return self.toVerilog("")
    
    def toVerilog(self, name):
        iostring = ".out(" + (self.output.signal if self.output.name == "UN-NAMED" else self.output.name) + ")"
        for j in range(self.num_inputs):
            iostring = iostring + ", .in" + (str(j) if self.num_inputs > 1 else "") + "(" + (self.inputs[j].signal if self.inputs[j].name == "UN-NAMED" else self.inputs[j].name) + ")"
        return self.__class__.__name__.lower() + str(self.num_inputs) + "$ " + name + "(" + iostring + ");"

class Wire:
    def __init__(self, signal):
        self.signal = signal
        self.drivenby = None
        self.driving = []
        self.name = "UN-NAMED"
    
    def __repr__(self):
        return "Wire of Signal " + self.signal
    
    def toVerilog(wirelist):
        wirestring = "w0"
        wirelist[0].name = "w0"
        for j in range(1, len(wirelist)):
            wirestring = wirestring + ", w" + str(j)
            wirelist[j].name = "w" + str(j)
        return "wire " + wirestring + ";"

def calcCriticalPathDelay(inputwires, outputwires):
    criticalpath = []
    def calcMaxDelayFromWire(w, delay, outputwires):
        if w in outputwires:
            criticalpath.append(w)
            return delay
        else:
            return max([calcMaxDelayFromWire(conn.output, delay+conn.delay, outputwires) for conn in w.driving])
    return max([calcMaxDelayFromWire(i, 0, outputwires) for i in inputwires])



class Nand(Gate):
    def __init__(self, inputs, num_inputs, output):
        if num_inputs == 4:
            super().__init__(inputs, 4, output, 0.25)
        elif num_inputs == 3 or num_inputs == 2:
            super().__init__(inputs, num_inputs, output, 0.2)
        else:
            print("<<<ERROR:::INCORRECT NUMBER OF INPUTS PROVIDED TO NAND GATE>>>")
            exit()
        gensignal = "&~("
        for i in inputs:
            i.driving.append(self)
            gensignal = gensignal + i.signal
        output.drivenby = self
        output.signal = gensignal + ")"

class And(Gate):
    def __init__(self, inputs, num_inputs, output):
        self.num_inputs = num_inputs
        if num_inputs == 4:
            super().__init__(inputs, 4, output, 0.40)
        elif num_inputs == 3 or num_inputs == 2:
            super().__init__(inputs, num_inputs, output, 0.35)
        else:
            print("<<<ERROR:::INCORRECT NUMBER OF INPUTS PROVIDED TO AND GATE>>>")
            exit()
        gensignal = "&("
        for i in inputs:
            i.driving.append(self)
            gensignal = gensignal + i.signal
        output.drivenby = self
        output.signal = gensignal + ")"
    
    def toNand(self):
        new_wires = [Wire("floating")]
        new_gates = [Nand(self.inputs, self.num_inputs, new_wires[0]), Inv(new_wires[0], self.output)]
        return new_wires, new_gates

    def toNor(self):
        new_wires = [Wire("floating"), Wire("floating")]
        new_gates = [Inv(self.inputs[0], new_wires[0]), Inv(self.inputs[1], new_wires[1]), Nor(new_wires, self.num_inputs, self.output)]
        return new_wires, new_gates

class Nor(Gate):
    def __init__(self, inputs, num_inputs, output):
        self.num_inputs = num_inputs
        if num_inputs == 4:
            super().__init__(inputs, 4, output, 0.35)
        elif num_inputs == 3:
            super().__init__(inputs, 3, output, 0.25)
        elif num_inputs == 2:
            super().__init__(inputs, 2, output, 0.2)
        else:
            print("<<<ERROR:::INCORRECT NUMBER OF INPUTS PROVIDED TO NOR GATE>>>")
            exit()
        gensignal = "|~("
        for i in inputs:
            i.driving.append(self)
            gensignal = gensignal + i.signal
        output.drivenby = self
        output.signal = gensignal + ")"

class Or(Gate):
    def __init__(self, inputs, num_inputs, output):
        self.num_inputs = num_inputs
        if num_inputs == 4:
            super().__init__(inputs, 4, output, 0.50)
        elif num_inputs == 3:
            super().__init__(inputs, 3, output, 0.40)
        elif num_inputs == 2:
            super().__init__(inputs, 2, output, 0.35)
        else:
            print("<<<ERROR:::INCORRECT NUMBER OF INPUTS PROVIDED TO OR GATE>>>")
            exit()
        gensignal = "|("
        for i in inputs:
            i.driving.append(self)
            gensignal = gensignal + i.signal
        output.drivenby = self
        output.signal = gensignal + ")"
    
    def toNand(self):
        new_wires = [Wire("floating"), Wire("floating")]
        new_gates = [Inv(self.inputs[0], new_wires[0]), Inv(self.inputs[1], new_wires[1]), Nand(new_wires, self.num_inputs, self.output)]
        return new_wires, new_gates

    def toNor(self):
        new_wires = [Wire("floating")]
        new_gates = [Nor(self.inputs, self.num_inputs, new_wires[0]), Inv(new_wires[0], self.output)]
        return new_wires, new_gates

#class Xor(Gate):

#class Xnor(Gate):

class Inv(Gate):
    def __init__(self, input, output):
        super().__init__([input], 1, output, 0.15)
        input.driving.append(self)
        output.drivenby = self
        output.signal = "~(" + input.signal + ")"
