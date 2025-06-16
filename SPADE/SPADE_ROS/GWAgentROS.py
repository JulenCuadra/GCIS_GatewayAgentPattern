""" Authors: Ane López Mena & Maite López Mena """
import asyncio
import time
import rospy
from spade.agent import Agent
from spade.template import Template
from std_msgs.msg import String
from Behaviours.Gateway2AssetCommBehaviour import Gateway2AssetCommBehaviour
from Behaviours.Asset2GatewayCommBehaviour import Asset2GatewayCommBehaviour

# ========================================================================== #
#                              ** GW AGENT ROS **                            #
# ========================================================================== #
class GWAgentROS(Agent):

    def __init__(self, jid, password):
        Agent.__init__(self, jid, password)
        self.id = str(jid)

    async def setup(self):
        print("[" + self.id + "] [GWAgentROS] entering setup")

        # Variables de gestión del estado del transporte
        self.state = "IDLE"

        # Se ejecuta un nodo ROS correspondiente al GWAgentROS
        rospy.init_node('GWAgentROS', anonymous=True)

        # Se crean además dos nodos:
        #   1) Un PUBLISHER, que dará la señal de comienzo del servicio por el tópico (coordinateIDLE)
        self.pub = rospy.Publisher('/coordinateIDLE', String, queue_size=10)

        #   2) Otro PUBLISHER, que comunicará el destino o coordenada a la que debe desplazarse el transporte.
        #   Utiliza para ello el tópico /coordinate
        self.pubCoord = rospy.Publisher('/coordinate', String, queue_size=10)  # Coordinate, queue_size=10)

        # Instancia el comportamiento 'Gateway2AssetCommBehaviour' para transmitir datos al transporte
        g2acb = Gateway2AssetCommBehaviour(self)

        template = Template()
        template.metadata = {'performative': 'REQUEST',
                             'ontology': 'asset_service'}

        # Añade el comportamiento al agente
        self.add_behaviour(g2acb, template)
        print("[" + self.id + "] [GWAgentROS] adding Gateway2AssetCommBehaviour")

        # Instancia el comportamiento 'Asset2GatewayCommBehaviour' para transmitir datos al transporte
        a2gcb = Asset2GatewayCommBehaviour(self)

        # Añade el comportamiento al agente
        self.add_behaviour(a2gcb)
        print("[" + self.id + "] [GWAgentROS] adding Asset2GatewayCommBehaviour")

