import logging
from spade.agent import Agent
from spade.template import Template
from spade.behaviour import FSMBehaviour, State

from Behaviours.AssetManagementBehaviour import AssetManagementBehaviour
from Behaviours.BootingBehaviour import BootingBehaviour
from Behaviours.RunningBehaviour import RunningBehaviour
from Behaviours.StoppingBehaviour import StoppingBehaviour
from Behaviours.NegotiationBehaviour import NegotiationBehaviour

# Definir los estados del FSM del ResourceAgent
STATE_ONE = "BOOTING"
STATE_TWO = "RUNNING"
STATE_THREE = "STOPPING"

_logger = logging.getLogger(__name__)

# ========================================================================== #
#                            ** RESOURCE AGENT **                            #
# ========================================================================== #
class ResourceAgent(Agent):

    async def setup(self):
        print("\n[ResourceAgent] entering setup")

        # Lista debería ser cargada a través del SRA con dispositivos disponibles
        self.targets = []

        # El comportamiento FSM implementa 2 métodos:

        # Instanciar el comportamiento FSM para el agente
        fsm = FSMBehaviour()

        # Cada estado del FSM, debe estar definido con un STRING y una clase STATE
        fsm.add_state(name=STATE_ONE, state=self.StateBooting(), initial=True)
        fsm.add_state(name=STATE_TWO, state=self.StateRunning())
        fsm.add_state(name=STATE_THREE, state=self.StateStopping())

        # Las transiciones definen de qué estado a que otro estado está permitido pasar
        fsm.add_transition(source=STATE_ONE, dest=STATE_TWO)
        fsm.add_transition(source=STATE_TWO, dest=STATE_THREE)

        # Añadir comportamiento FSM al agente
        self.add_behaviour(fsm)

        print("\n[ResourceAgent] exiting setup")


# =========================================================================
# El comportamiento FSM, incluye en su interior, ESTADOS y las TRANSICIONES
# entre estos estados. Esta es una subclase de CyclicBehaviour
    class FSMBehaviour(FSMBehaviour):

        # ON_START: Se ejecuta ANTES del primer estado del FSM
        async def on_start(self):
            print(f"    ** FSM starting at state --> {self.current_state}")

        # ON_STOP: Se ejecuta DESPUÉS del último estado del FSM
        async def on_end(self):
            print(f"    ** FSM finished at state --> {self.current_state}")
            await self.agent.stop()

# ========================================================================== #
#                           ** ESTADO 1: BOOTING **                          #
# ========================================================================== #
    class StateBooting(State):
        async def run(self):
            print("[" + self.agent.id + "] [ResourceAgent] entering StateBooting")

            # Este comportamiento llevará a cabo las tareas de inicialización
            bb = BootingBehaviour(self.agent)

            #  Añade el comportamiento 'BootingBehaviour' al agente.
            self.agent.add_behaviour(bb)

            # Esperar a que el comportamiento de inicialización acabe (BLOQUEO)
            await bb.join()

            print("[" + self.agent.id + "] [ResourceAgent] transitioning to StateRunning")
            # Método para indicar la transición al próximo estado: RUNNING
            self.set_next_state(STATE_TWO)

# ========================================================================== #
#                           ** ESTADO 2: RUNNING **                          #
# ========================================================================== #
    class StateRunning(State):
        async def run(self):
    #   Un estado RUNNING compuesto de 3 comportamientos:

    #   1)  [Negotiation Behaviour]
    #       Comportamiento que participa en las negociaciones para la
    #       asignación de servicios (‘comportamiento de negociación’).
            print("[Negotiation Behaviour]")
            print("             |___ Ready for negotiation")

    #       [PLANTILLAS / TEMPLATES]
    #       Son necesarias para gestionar la correcta recepción de los mensajes ACL
            template = Template()
            template.thread = "MY_VALUE"

            template2 = Template()
            template2.thread = "WINNER"

            # Crear una instancia de NegotiationBehaviour
            nb = NegotiationBehaviour(self.agent)

            # Añade el comportamiento 'NegotiationBehaviour' al agente
            # Añade además las plantillas de mensaje
            self.agent.add_behaviour(nb, template | template2)

    #   2)  [Running Behaviour]
    #       Comportamiento para gestionar las peticiones de servicio que llegan de la
    #       fábrica (mensajes ACL solicitando que la máquina ejecute un servicio determinado)
            print("[Running Behaviour]")
            print("          |___ Waiting for service requests...\n")

            # Crear una instancia de RunningBehaviour
            rb = RunningBehaviour(self.agent)

            # Añade el comportamiento 'RunningBehaviour' al agente
            self.agent.add_behaviour(rb)

    #   3)  [Asset Management Behaviour]
    #       Comportamiento para gestionar el propio comportamiento del activo.
    #       Como parte de la gestión del comportamiento del activo, hay que definir una
    #       interfaz en la que se declaren dos métodos (sendDataToAsset y rcvDataFromAsset) para
    #       estandarizar la interacción entre un agente y su correspondiente agente pasarela.
            print(str(self.agent.id) + ":         [AssetManagement Behaviour]")
            print("             |___ Waiting for processing services...\n")

            # Crear una instancia de AssetManagementBehaviour
            amb = AssetManagementBehaviour(self.agent)

            # Añade el comportamiento al estado y sus plantillas
            self.agent.add_behaviour(amb)

            # Si terminan ambos comportamientos, pasar al siguiente estado
            if (rb.is_done() and nb.is_done()):
                self.set_next_state(STATE_THREE)

# ========================================================================== #
#                           ** ESTADO 3: STOPPING **                         #
# ========================================================================== #
    class StateStopping(State):
        async def run(self):
            print("## STATE 3: STOPPING ##")
            sb = StoppingBehaviour(self.agent)
            self.agent.add_behaviour(sb)
            print("     [Stopping Behaviour]")
            print("         |___ Stopping MachineAgent...")
            # No se ha indicado un estado final, por lo que este se considera el último
