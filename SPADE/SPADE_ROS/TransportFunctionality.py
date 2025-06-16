""" Authors: Ane López Mena & Maite López Mena """
import asyncio
import time
import random
import string
from spade.message import Message
from spade.template import Template
from RAInterface import RAInterface
from Agents.GWAgentROS import GWAgentROS
from Behaviours.NegotiationBehaviour import NegotiationBehaviour

# ========================================================================== #
#                      ** TRANSPORT FUNCTIONALITY **                           #
# ========================================================================== #
# Esta clase heredará dos métodos de la interfaz 'RAInterface'
#   1) rcvDataFromAsset
#   2) sendDataToAsset
class TransportFunctionality(RAInterface):
    #   [BOOTING BEHAVIOUR]
    async def init(self, myAgent):
        # Método de inicialización del agente TRANSPORTE
        print("[" + myAgent.id + "] [TransportFunctionality, init] booting")

        # Inicializar variables:
        #   1) Flag WIP (WorkInProgress)
        self.WIP = False
        #   2) Estado inicial / predefinido
        self.state = "ACTIVE"

        # Guardar JID + password de GWAgentROS
        gw_jid = "gwagentros_" + myAgent.id.split('_')[1]
        myAgent.gw_jid = gw_jid
        passwd = "upv123"

        # Instanciar el GWAgentROS para comunicarse con al Asset Físico (AGV).
        ga = GWAgentROS(gw_jid, passwd)
        await ga.start()

        print("[" + myAgent.id + "] [TransportFunctionality, init] booting finished")

# ==========================================================================
#   [RUNNING BEHAVIOUR]
    async def execute(self, behav, myAgent):
        # Método de ejecución de las funcionalidades del agente trasnporte. Aquí, el agente se
        # quedará a la escucha de mensajes, y tras recibir una petición, la añadirá al plan de transporte
        print("[" + myAgent.id + "] [TransportFunctionality, execute] running")

        if not myAgent.ready:
            myAgent.ready = True

        # A espera de recibir mensajes
        receivedMsg = await behav.receive(timeout=60)
        if receivedMsg:
            if receivedMsg.metadata == {'performative': 'REQUEST',
                                        'ontology': 'agent_service'}:
                print("\n[" + myAgent.id + "] [TransportFunctionality, execute] message from "
                      + str(receivedMsg.sender) + ": {}".format(receivedMsg.body))

                # Añadir petición al plan de transporte
                myAgent.transportPlan.append(receivedMsg.body)
                print("[" + myAgent.id + "] [TransportFunctionality, execute] request added to TransportPlan: " + str(myAgent.transportPlan))

            elif 'CFP' in receivedMsg.metadata['performative'] \
                and 'negotiation' in receivedMsg.metadata['ontology']:
                thread = receivedMsg.metadata['thread']
                print("\n[" + myAgent.id + "] [TransportFunctionality, execute, " + thread + "] CFP message from " + str(receivedMsg.sender))

                template = Template()
                template.metadata = {'performative': 'PROPOSE',
                                     'ontology': 'negotiation',
                                     'thread': thread}

                data = receivedMsg.body.split("#")
                contractors = data[0].split("=")[1]
                targets = contractors.strip('][').split(', ')
                criteria = data[1].split("=")[1]

                nb = NegotiationBehaviour(myAgent, thread, targets, criteria)
                print("[" + myAgent.id + "] [TransportFunctionality, execute, " + thread + "] NegotiationBehaviour instantiated")

                myAgent.add_behaviour(nb, template)
                print("[" + myAgent.id + "] [TransportFunctionality, execute, " + thread + "] adding NegotiationBehaviour")

        else:
            # No ha recibido mensaje en un intervalo de 360 segundos
            print("[" + myAgent.id + "] [TransportFunctionality, execute] No message received in a while")

# ============================================================================================================
#   [NEGOTIATION BEHAVIOUR]
    async def negotiation(self, behav, myAgent):
        # El algoritmo de negociación, tiene 4 fases[0-3]:

        if (behav.criteria == "battery"):
            myValue = myAgent.battery

        if (behav.step == 0):
            await asyncio.sleep(1) # Espera para asegurar que resto de agentes listos para negociar

            for jid in behav.targets:
                # Quitar caracter "'"
                jid = jid.replace("'", "")

                # Si no es el JID propio, enviar mensaje
                if (jid != myAgent.id):
                    msg2send = Message(to=str(jid).replace("'", ""),
                                       sender=str(myAgent.id),
                                       body=str(str(myAgent.id) + "," + str(myValue)))

                    # Settea thread como 'MY_VALUE'
                    msg2send.metadata = {'performative': 'PROPOSE',
                                         'ontology': 'negotiation',
                                         'thread': behav.thread}

                    # Envía al mensaje al otro transport agent
                    print("[" + myAgent.id + "] [TransportFunctionality, negotiation, " + behav.thread + "] PROPOSAL message to " + str(jid))
                    await behav.send(msg2send)

            # Pasar a la siguiente etapa
            behav.step = 1

        if (behav.step == 1):
            replyMsg = await behav.receive(timeout=60)
            if replyMsg:
                sender_jid = str(replyMsg.body.split(",")[0])
                sender_value = float(replyMsg.body.split(",")[1])
                print("\n[" + myAgent.id + "] [TransportFunctionality, negotiation, " + behav.thread + ", step=1] PROPOSAL message from " + str(sender_jid) + ": battery " + str(sender_value))

                if (sender_value >= myValue): # Sale de la negociación
                    print("[" + myAgent.id + "] [TransportFunctionality, negotiation, " + behav.thread + ", step=1] negotiation lost")
                    behav.step = 3

                behav.replyNum = behav.replyNum + 1

                if (behav.replyNum >= len(behav.targets)-1):
                    if (behav.step == 3):
                        pass
                    else:
                        # Si, una vez recibidos todos los mensajes, el valor propio sigue siendo el mejor,
                        # se salta al paso 2. Se declara el transport agent como ganador
                        behav.step = 2

            else:
                # No ha recibido mensaje en un intervalo de 360 segundos
                print("[" + myAgent.id + "] [TransportFunctionality, negotiation, " + behav.thread + ", step=1] No message received in a while\n")

        if (behav.step == 2):
            print("[" + myAgent.id + "] [TransportFunctionality, negotiation, " + behav.thread + ", step=2] negotiation won")

            # Se notifica que hay ganador mediante el thread 'WINNER'
            msg2send = Message(to=myAgent.machine_jid, sender=myAgent.id, body='WINNER')
            msg2send.metadata = {'performative': 'INFORM',
                                 'ontology': 'negotiation',
                                 'thread': behav.thread}

            await behav.send(msg2send)
            print("[" + myAgent.id + "] [TransportFunctionality, negotiation, " + behav.thread + ", step=2] INFORM message to " + myAgent.machine_jid + ": " + msg2send.body)

            behav.step = 0
            behav.kill(exit_code=1)

        if (behav.step == 3):
            behav.step = 0
            behav.kill(exit_code=1)


# ============================================================================================================
#   [ASSET MANAGEMENT BEHAVIOUR]
    async def rcvDataFromAsset(self, behav, myAgent):
        # Evalúa el valor de un flag de “trabajo en proceso” (WIP) para determinar
        # si un recurso físico está disponible.
        if self.WIP:
            print("\n[" + myAgent.id + "] [TransportFunctionality, rcvDataFromAsset] wait message from " + myAgent.gw_jid)
            receivedMsg = await behav.receive(timeout=60)
            if receivedMsg:
                print("[" + myAgent.id + "] [TransportFunctionality, rcvDataFromAsset] in warehouse")

                # Obtener la tarea finalizada
                task = myAgent.transportPlan[0]
                print("[" + myAgent.id + "] [TransportFunctionality, rcvDataFromAsset] task " + str(task) + " finished")

                # Quitar tarea del plan del transporte, puesto que ya se ha realizado con éxito
                myAgent.transportPlan.pop(0)
                print("[" + myAgent.id + "] [TransportFunctionality, rcvDataFromAsset] request removed from TransportPlan: " + str(myAgent.transportPlan))

                # Marcar el recurso como DISPONIBLE
                self.WIP = False

                # Obtener tipo de servicio
                taskType = task.split(":")[0]

                # Si la tarea realizada ha sido de tipo 'DELIVERY'
                if (taskType == "DELIVERY"):
                    # Enviar una solicitud de servicio a MACHINE AGENT

                    # Generar el mensaje para enviar
                    msg2send = Message(to=myAgent.machine_jid, sender=myAgent.id, body=str(task))
                    msg2send.metadata = {'performative': 'REQUEST',
                                         'ontology': 'agent_service'}
                    # Envía al mensaje
                    await behav.send(msg2send)
                    print("[" + myAgent.id + "] [TransportFunctionality, rcvDataFromAsset] service request to " + myAgent.machine_jid + ": " + task)

                # Si la tarea realizada ha sido de tipo 'DELIVERY'
                elif (taskType == "COLLECTION"):
                    # Enviar un mensaje de estado a MACHINE AGENT

                    # Generar el mensaje para enviar
                    msg2send = Message(to=myAgent.machine_jid, sender=myAgent.id, body="IN WAREHOUSE")
                    msg2send.metadata = {'performative': 'INFORM',
                                         'ontology': 'asset_status'}
                    # Envía al mensaje
                    await behav.send(msg2send)
                    print("[" + myAgent.id + "] [TransportFunctionality, rcvDataFromAsset] update " + myAgent.machine_jid + ": {}".format(msg2send.body))
            else:
                # No ha recibido mensaje en un intervalo de 360 segundos
                print("[" + myAgent.id + "] [TransportFunctionality, rcvDataFromAsset] No message received in a while")

# ----------------------------------------------------------------------------------------------------
    async def sendDataToAsset(self, behav, myAgent):
        # Evalúa el valor de un flag de “trabajo en proceso”(WIP) para determinar
        # si un recurso físico está disponible. Si es así, también comprueba las peticiones de
        # servicio pendientes relacionadas con el recurso (plan de transporte).
        # Si se dan esas condiciones, la información relativa a la siguiente petición de servicio
        # se envía al gateway (pasarela). Una vez se haya envíado la información, el flag “trabajo
        # en proceso” se activa para bloquear el envío de nueva información, hasta que el servicio actual
        # se haya completado (WIP=True).

        # Procesar las tareas del plan de transporte
        if (not self.WIP and len(myAgent.transportPlan) > 0):

            # Marcar el transporte como OCUPADO
            self.WIP = True

            # Coge la primera tarea de la lista
            task = myAgent.transportPlan[0]
            print("[" + myAgent.id + "] [TransportFunctionality, sendDataToAsset] next task in queue: " + task)

            # Identifica el tipo de tarea
            taskType = task.split(":")[0]

            # Instancia el mensaje a enviar:
            msg2send = Message(to=myAgent.gw_jid, sender=myAgent.id, body=str(taskType))
            msg2send.metadata = {'performative': 'REQUEST',
                                 'ontology': 'asset_service'}

            # Envía el mensaje al GWAgentROS
            await behav.send(msg2send)
            print("[" + myAgent.id + "] [TransportFunctionality, sendDataToAsset] service request to " + myAgent.gw_jid + ": " + msg2send.body)

# ============================================================================================================
#   [STOPPING BEHAVIOUR]
    def stop(self):
        print("Transport status: STOP")

# ============================================================================================================
#   [IDLE BEHAVIOUR]
    def idle(self):
        print("Transport status: IDLE")
