""" Authors: Ane López Mena & Maite López Mena """
import asyncio

from spade.behaviour import CyclicBehaviour

# ========================================================================== #
#                      ** ASSET MANAGEMENT BEHAVIOUR **                      #
# ========================================================================== #
# Define el comportamiento del Agente como "CyclicBehaviour"
class AssetManagementBehaviour(CyclicBehaviour):

    def __init__(self, a):
        # Heredamos el init de la clase super
        super().__init__()

        # Definir atributos propios del agente:
        #  1) Instancia del agente que ejecuta el comportamiento
        self.myAgent = a

    async def run(self):
        await self.myAgent.functionality.sendDataToAsset(self, self.myAgent)
        await self.myAgent.functionality.rcvDataFromAsset(self, self.myAgent)

    async def on_end(self):
        print("[" + self.agent.id + "] [AssetManagementBehaviour, on_end] amb kaput")