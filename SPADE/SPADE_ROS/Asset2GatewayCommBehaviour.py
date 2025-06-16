""" Authors: Ane López Mena & Maite López Mena """
import rospy
from std_msgs.msg import String
from spade.behaviour import CyclicBehaviour

# ========================================================================== #
#             ** RECEIVE DATA FROM TRANSPORT BEHAVIOUR **                    #
# ========================================================================== #
# Define el comportamiento del Agente como "CyclicBehaviour"
class Asset2GatewayCommBehaviour(CyclicBehaviour):

    def __init__(self, a):
        # Heredamos el init de la clase super
        super().__init__()
        # Definir atributos propios del agente:
        #  1) Instancia del agente que ejecuta el comportamiento
        self.myAgent = a

        # Crea un nodo SUBSCRIBER, que se quedará a la escucha por el tópico /status
        # y notificará al agente del estado del transporte
        rospy.Subscriber('/status', String, self.callback)

    # ------------------------------------------------------------------
    def callback(self, data):
        # Este método se ejecutará cada vez que se publiquen datos por el tópico /status

        # Actualiza el estado del transporte
        self.myAgent.state = str(data.data)
        print("[" + self.myAgent.id + "] [Asset2GatewayCommBehaviour] turtlebot's new state: " + str(self.myAgent.state))

    # ------------------------------------------------------------------
    async def run(self):
        pass

