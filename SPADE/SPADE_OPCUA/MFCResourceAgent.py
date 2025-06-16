""" Authors: Ane López Mena & Maite López Mena """
import logging
from spade.template import Template
from Agents.ResourceAgent import ResourceAgent
from spade.behaviour import FSMBehaviour, State
from Behaviours.IdleBehaviour import IdleBehaviour
from Behaviours.RunningBehaviour import RunningBehaviour
from Behaviours.NegotiationBehaviour import NegotiationBehaviour
from Behaviours.AssetManagementBehaviour import AssetManagementBehaviour

# Se definen los estados del FSM
STATE_ONE = "BOOTING"
STATE_TWO = "RUNNING"
STATE_THREE = "STOPPING"
STATE_FOUR = "IDLE"

_logger = logging.getLogger(__name__)

# ========================================================================== #
#                          ** MFC RESOURCE AGENT **                          #
# ========================================================================== #
class MFCResourceAgent(ResourceAgent):

    def __init__(self, jid, password, targets):
        print("[" + jid + "] [MFCResourceAgent] entering init")
        super().__init__(jid, password)
        self.targets = targets

    # Heredado de la clase ResourceAgent, hace override del metodo de la clase madre
    async def setup(self):
        print("[" + str(self.jid) + "] [MFCResourceAgent] entering setup")

        # El comportamiento FSM implementa 2 métodos, Añadir estados y añadir transiciones
        # Instanciar el comportamiento FSM para el agente
        fsm = FSMBehaviour()

        # Se define cada estado del FSM con un STRING y una clase STATE
        fsm.add_state(name=STATE_ONE, state=self.StateBooting(), initial=True)
        fsm.add_state(name=STATE_TWO, state=self.StateRunning())
        fsm.add_state(name=STATE_THREE, state=self.StateStopping())
        fsm.add_state(name=STATE_FOUR, state=self.StateIdle())

        # Se definen las transiciones entre los posibles estados del FSM
        fsm.add_transition(source=STATE_ONE, dest=STATE_TWO)
        fsm.add_transition(source=STATE_TWO, dest=STATE_THREE)
        fsm.add_transition(source=STATE_TWO, dest=STATE_FOUR)
        fsm.add_transition(source=STATE_FOUR, dest=STATE_TWO)
        fsm.add_transition(source=STATE_FOUR, dest=STATE_THREE)

        # Añadir comportamiento FSM al agente
        self.add_behaviour(fsm)

        print("[" + str(self.jid) + "] [MFCResourceAgent] exiting setup")

    # ========================================================================== #
    #                           ** ESTADO 1: BOOTING **                          #
    # ========================================================================== #
    # Heredado de la clase ResourceAgent

    # ========================================================================== #
    #                           ** ESTADO 2: RUNNING **                          #
    # ========================================================================== #
    # Heredado de la clase ResourceAgent, override de la clase madre
    class StateRunning(State):

        async def run(self):
            print("[" + self.agent.id + "] [MFCResourceAgent] entering StateRunning")

    # Este estado de RUNNING está compuesto de 3 comportamientos:
        #   1)  [Negotiation Behaviour]
        #   Comportamiento que participa en las negociaciones para la
        #   asignación de servicios (‘comportamiento de negociación’).
            nb = NegotiationBehaviour(self.agent)

            template = Template()
            template.metadata = {'performative': 'INFORM',
                                 'ontology': 'negotiation'}

            self.agent.add_behaviour(nb, template)
            print("[" + self.agent.id + "] [MFCResourceAgent] adding NegotiationBehaviour")

        #   2) [Running Behaviour]
        #   Comportamiento para gestionar las peticiones de servicio que llegan de la
        #   fábrica (mensajes ACL solicitando que la máquina ejecute un servicio determinado)
            rb = RunningBehaviour(self.agent)

            template = Template()
            template.metadata = {'performative': 'REQUEST',
                                 'ontology': 'agent_service'}

            self.agent.add_behaviour(rb, template)
            print("[" + self.agent.id + "] [MFCResourceAgent] adding RunningBehaviour")

        #   3)  [Asset Management Behaviour]
        #   Comportamiento para gestionar el propio comportamiento del activo.
        #   Como parte de la gestión del comportamiento del activo, hay que definir una
        #   interfaz en la que se declaren dos métodos (sendDataToAsset y rcvDataFromAsset) para
        #   estandarizar la interacción entre un agente y su correspondiente agente pasarela.
            amb = AssetManagementBehaviour(self.agent)

            template = Template()
            template.metadata = {'performative': 'INFORM',
                                 'ontology': 'asset_status'}

            self.agent.add_behaviour(amb, template)
            print("[" + self.agent.id + "] [MFCResourceAgent] adding AssetManagementBehaviour")

            # Si este comportamiento se detiene, volver a iniciarlo
            if (amb.is_killed()):
                amb.start()

            # Si terminan los tres comportamientos, pasar al siguiente estado
            if (rb.is_done() and nb.is_done() and amb.is_done()):
                self.set_next_state(STATE_THREE)

    # ========================================================================== #
    #                           ** ESTADO 3: STOPPING **                         #
    # ========================================================================== #
    # Heredado de la clase ResourceAgent

    # ========================================================================== #
    #                             ** ESTADO 4: IDLE **                           #
    # ========================================================================== #
    class StateIdle(State):
        async def run(self):
            print("[" + self.agent.id + "] entering StateIdle")

            ib = IdleBehaviour(self.agent)
            self.agent.add_behaviour(ib)
            print("[" + self.agent.id + "] adding AssetManagementBehaviour")

            # No se ha indicado un estado final, por lo que este se considera el último

