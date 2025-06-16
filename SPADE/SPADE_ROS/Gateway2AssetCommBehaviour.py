""" Authors: Ane López Mena & Maite López Mena """
import asyncio
import time
import logging
from spade.message import Message
from spade.behaviour import CyclicBehaviour

# ========================================================================== #
#                  ** SEND DATA 2 TRANSPORT BEHAVIOUR **                     #
# ========================================================================== #
# Define el comportamiento del Agente como "CyclicBehaviour", para enviar los
# mensajes recibidos del TransportAgent al Transporte implementado mediante nodos ROS
class Gateway2AssetCommBehaviour(CyclicBehaviour):

    def __init__(self, a):
        # Heredamos el init de la clase super
        super().__init__()
        # Definir atributos propios del agente:
        #  1) Instancia del agente que ejecuta el comportamiento
        self.myAgent = a
        #  2) Flag de control de trabajo en progreso (WorkInProgress)
        self.WIP = False

    # ------------------------------------------------------------------
    async def run(self):
        # Si el transporte no está ocupado
        if not self.WIP:
            # Queda a la espera de recibir un mensaje
            msg = await self.receive(timeout=60)
            if msg:
                print("\n[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] message from " + str(msg.sender) + ": " + msg.body)

                # Si el thread del mensaje recibido es DELIVERY o COLLECTION
                if msg.body in ["DELIVERY", "COLLECTION"]:
                    # Marcar el flag para indicar trabajo en proceso
                    self.WIP = True

                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] agent state: " + self.myAgent.state)

                    self.agent.pub.publish("GO") # pasar a LOCALIZATION
                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] send localization message")
                    await asyncio.sleep(1)

                    # esperamos LOCALIZATION (IDLE si agente reiniciado)
                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] agent state: " + self.myAgent.state)

                    while self.myAgent.state == "LOCALIZATION": # mientras se está en LOCALIZATION
                        await asyncio.sleep(0.1)
                        if self.myAgent.state == "ACTIVE":
                            break

                    # esperamos ACTIVE (IDLE si agente reiniciado)
                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] agent state: " + self.myAgent.state)

                    # Se le ordena a un publicista que publique las coordenadas objetivo
                    # Para este ejemplo, son coordenadas estáticas
                    # que representan la posición fija e invariable del almacén
                    self.myAgent.pubCoord.publish("1.43,0.59") # pasar a operative
                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] send warehouse coordinates")
                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] wait while moving to warehouse")

                    while self.myAgent.state in ["IDLE", "ACTIVE"]: # por si se sigue en IDLE o ACTIVE
                        await asyncio.sleep(0.1)
                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] agent state: " + self.myAgent.state)

                    while not self.myAgent.state == "ACTIVE": # mientras se está en OPERATIVE
                        await asyncio.sleep(0.1)
                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] agent state: " + self.myAgent.state)

                    # Avisar a TransportAgent de que el robot ya ha llegado a la máquina.
                    msg2 = Message(to=str(msg.sender), sender=self.myAgent.id, body="IN WAREHOUSE")
                    msg2.metadata = {'performative': 'INFORM',
                                     'ontology': 'asset_status'}
                    await self.send(msg2)
                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] update " + str(msg2.to) + ": " + msg2.body)

                    # Coordenadas estáticas que representan la posición de ORIGEN del turtlebot3
                    self.myAgent.pubCoord.publish("-1.65,-0.56")
                    print("\n[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] send collection/delivery point coordinates")
                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] wait while moving to collection/delivery point")

                    while self.myAgent.state == "ACTIVE":
                        await asyncio.sleep(0.1)
                    print("[" + self.myAgent.id + "] agent state: " + self.myAgent.state)

                    while not self.myAgent.state == "ACTIVE":
                        await asyncio.sleep(0.1)
                    print("[" + self.myAgent.id + "] agent state: " + self.myAgent.state)

                    print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] ready")

                    self.WIP = False

            else:
                # No ha recibido mensaje en un intervalo de 360 segundos
                print("[" + self.myAgent.id + "] [Gateway2AssetCommBehaviour] No message received in a while")