""" Authors: Ane López Mena & Maite López Mena """
from spade.behaviour import OneShotBehaviour

# ========================================================================== #
#                          ** BOOTING BEHAVIOUR **                           #
# ========================================================================== #
# Define el comportamiento del Agente como "OneShotBehaviour"
class BootingBehaviour(OneShotBehaviour):

    def __init__(self, a):
        # Heredamos el init de la clase super
        super().__init__()

        # Definir atributos propios del agente:
        #  1) Instancia del agente que ejecuta el comportamiento
        self.myAgent = a

    # ------------------------------------------------------------------
    async def run(self):
        print("\n[" + self.agent.id + "] [BootingBehaviour, run]")
        await self.myAgent.functionality.init(self.myAgent)
