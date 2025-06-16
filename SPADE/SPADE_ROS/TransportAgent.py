""" Authors: Ane López Mena & Maite López Mena """
from random import randint
from Agents.ResourceAgent import *
from Functionalities.TransportFunctionality import *
from Agents.MFCResourceAgent import MFCResourceAgent

# ========================================================================== #
#                             ** TRANSPORT AGENT **                          #
# ========================================================================== #

class TransportAgent(MFCResourceAgent):

    def __init__(self, jid, password, machine_jid, battery=99):
        print("[" + jid + "] [TransportAgent] entering init")

        self.ready = False
        MFCResourceAgent.__init__(self, jid, password, machine_jid)

        # Definir atributos propios del agente Transporte:
        #  1) JID del agente
        self.id = str(jid)
        #  2) Ganador de negociación, por defecto en FALSE
        self.winner = False
        #  3) Genera un porcentaje de batería aleatorio entre 1-100
        self.battery = battery
        print("[" + jid + "] [TransportAgent] battery level: " + str(self.battery) + "%")

        # Definir el listado de tareas del transporte: TRANSPORT PLAN
        # Según reciba peticiones, se irán poniendo en cola y ejecutando en orden (FIFO)
        self.transportPlan = []

        # Definir las funcionalidades propias de un recurso TRANSPORTE
        self.functionality = TransportFunctionality()

        print("[" + jid + "] [TransportAgent] exiting init")
