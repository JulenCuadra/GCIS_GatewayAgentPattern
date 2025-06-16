
import logging
import time
from opcua import ua
from spade.agent import Agent
from spade.template import Template
from Behaviours.AssetCommBehaviour import AssetCommBehaviour

# ========================================================================== #
#                             ** GW AGENT OPCUA **                           #
# ========================================================================== #
class GWAgentOPCUA(Agent):

    def __init__(self, jid, password):
        Agent.__init__(self, jid, password)
        # Definir atributos propios del agente Transporte:
        #  1) JID del agente
        self.id = str(jid)

        #print("[" + self.id + "] setting OPC UA client")
        #self.client = Client("opc.tcp://192.168.0.101:4840")
        #print("[" + self.id + "] connecting to OPC UA server")
        #self.client.connect()

        # Llevar máquina a producción normal
        #self.machineSetUp()

        #self.client.close_session()

    async def setup(self):
        print("[" + self.id + "] [GWAgentOPCUA] entering setup")

        acb = AssetCommBehaviour(self)

        template = Template()
        template.metadata = {'performative': 'REQUEST',
                            'ontology': 'asset_service'}

        self.add_behaviour(acb, template)
        print("[" + self.id + "] [GWAgentOPCUA] adding AssetCommBehaviour")

    def machineSetUp(self):
        # Instanciar nodos
        node_AuxInit = self.client.get_node('ns=3;s="AuxInit"')
        node_Marcha = self.client.get_node('ns=3;s="Marcha"')

        # ------- Simular arranque de máquina
        node_AuxInit.set_attribute(ua.AttributeIds.Value, ua.DataValue(True))
        time.sleep(1)
        node_AuxInit.set_attribute(ua.AttributeIds.Value, ua.DataValue(False))

        # ------- Simular pulso de "Marcha"
        node_Marcha.set_attribute(ua.AttributeIds.Value, ua.DataValue(True))
        time.sleep(1)
        node_Marcha.set_attribute(ua.AttributeIds.Value, ua.DataValue(False))
