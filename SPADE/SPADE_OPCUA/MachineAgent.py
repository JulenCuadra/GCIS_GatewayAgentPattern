""" Authors: Ane López Mena & Maite López Mena """
from Agents.ResourceAgent import *
from Functionalities.MachineFunctionality import *
from Agents.MFCResourceAgent import MFCResourceAgent

# ========================================================================== #
#                             ** MACHINE AGENT **                            #
# ========================================================================== #
class MachineAgent(MFCResourceAgent):

    def __init__(self, jid, password, targets):
        print("[" + jid + "] [MachineAgent] entering init")

        self.ready = False
        MFCResourceAgent.__init__(self, jid, password, targets)

        # Definir atributos propios del agente Transporte:
        #  1) JID del agente
        self.id = str(jid)

        # Definir el listado de tareas de la máquina: MACHINE PLAN
        # Según reciba peticiones, se irán poniendo en cola y ejecutando en orden (FIFO)
        self.machinePlan = []

        # Definir las funcionalidades propias de un recurso MÁQUINA
        self.functionality = MachineFunctionality()

        print("[" + jid + "] [MachineAgent] exiting init")
