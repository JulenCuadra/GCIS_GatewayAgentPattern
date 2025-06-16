""" Authors: Ane López Mena & Maite López Mena """
import asyncio
import random
import time
import logging
from tqdm.asyncio import tqdm
import opcua.ua
from opcua import ua
from opcua import Client
from spade.message import Message
from spade.behaviour import CyclicBehaviour

# ========================================================================== #
#                          ** RECEIVE BEHAVIOUR **                           #
# ========================================================================== #
# Define el comportamiento del Agente como "CyclicBehaviour"
class AssetCommBehaviour(CyclicBehaviour):

    def __init__(self, a):
        # Heredamos el init de la clase super
        super().__init__()
        # Definir atributos propios del agente:
        #  1) Instancia del agente que ejecuta el comportamiento
        self.myAgent = a

    async def run(self):
        # Queda a la espera de recibir un mensaje
        msg = await self.receive(timeout=60)
        if msg:
            print("\n[" + self.myAgent.id + "] [AssetCommBehaviour] message from " + str(msg.sender) + ": " + msg.body)

            # Se extraen del mensaje recibido el tipo de servicio y la posición
            taskType = str(msg.body).split(":")[0]
            target = str(msg.body).split(":")[1]

            # Si el tipo de servicio es 'DELIVERY'
            if taskType == "DELIVERY":
                print("[" + self.myAgent.id + "] [AssetCommBehaviour] store package into shelf " + str(target))

                #result = await self.sendDataOPCUA(taskType, target)
                for _ in tqdm(range(5), desc="[" + self.myAgent.id + "] [AssetCommBehaviour] introducing package"):
                    await asyncio.sleep(1)
                result = "FINISHED"

                if (result == "FINISHED"):
                    print("[" + self.myAgent.id + "] [AssetCommBehaviour] package stored")

                    # Mensaje para actualizar plan de máquina
                    msg2Send = Message(to=str(msg.sender), sender=str(self.myAgent.id), body="STORED")
                    msg2Send.metadata = {'performative': 'INFORM',
                                         'ontology': 'asset_status'}

                    # Envía al mensaje al GWAgent
                    await self.send(msg2Send)
                    print("[" + self.myAgent.id + "] [AssetCommBehaviour] update " + str(msg.sender) + ": " + msg.body)

                else:
                    print("[" + self.myAgent.id + "] [AssetCommBehaviour] shelf " + str(target) +" is already occupied")

            else:
                # Si el tipo de servicio es 'COLLECTION'
                print("[" + self.myAgent.id + "] [AssetCommBehaviour] extract package from shelf " + str(target))

                #result = await self.sendDataOPCUA(taskType, target)
                for _ in tqdm(range(5), desc="[" + self.myAgent.id + "] [AssetCommBehaviour] extracting package"):
                    await asyncio.sleep(1)
                result = "FINISHED"

                if (result == "FINISHED"):
                    print("[" + self.myAgent.id + "] [AssetCommBehaviour] package extracted")

                    # Mensaje para actualizar plan de máquina
                    msg2Send = Message(to=str(msg.sender), sender=str(self.myAgent.id), body="EXTRACTED")
                    msg2Send.metadata = {'performative': 'INFORM',
                                         'ontology': 'asset_status'}

                    # Envía al mensaje al GWAgent
                    await self.send(msg2Send)
                    print("[" + self.myAgent.id + "] [AssetCommBehaviour] update " + str(msg.sender) + ": " + msg.body)

                else:
                    print("[" + self.myAgent.id + "] [AssetCommBehaviour] shelf No. " + str(target) + " empty")

        else:
            # No ha recibido mensaje en un intervalo de 360 segundos
            print("[" + self.myAgent.id + "] [AssetCommBehaviour] No message received in a while")

# ====================================================================

    async def sendDataOPCUA(self, serviceType, target):
    # En este método se realiza toda la lógica de lectura/escritura de nodos
    # publicados en la interfaz del servidor OPC UA

        print("[" + self.myAgent.id + "] [AssetCommBehaviour, SendDataOPCUA] set OPC UA client")
        self.myAgent.client = Client("opc.tcp://192.168.0.101:4840")
        print("[" + self.myAgent.id + "] [AssetCommBehaviour, SendDataOPCUA] connect to OPC UA server")
        self.myAgent.client.connect()

        # Instanciar nodos con los que se realizarán las operaciones rw
        node_Reset = self.myAgent.client.get_node('ns=3;s="Reset"')
        node_DejarCoger = self.myAgent.client.get_node('ns=3;s="DejarCoger"')
        node_Posicion = self.myAgent.client.get_node('ns=3;s="Posicion"')
        node_NewService = self.myAgent.client.get_node('ns=3;s="DB_OPCUA"."control_parameters"."Control_Flag_New_Service"')
        node_ServiceFinished = self.myAgent.client.get_node('ns=3;s="DB_OPCUA"."control_parameters"."Control_Flag_Service_Completed"')
        node_AlmacenOcupacion = self.myAgent.client.get_node('ns=3;s="Sensores"."AlmacenOcupacion"')

        print("[" + self.myAgent.id + "] [AssetCommBehaviour, SendDataOPCUA] check availability")
        busy = node_NewService.get_value()
        if busy:
            print("[" + self.myAgent.id + "] [AssetCommBehaviour, SendDataOPCUA] warehouse busy")
            while busy:
                espera = random.uniform(0, 1)
                print("[" + self.myAgent.id + "] waiting...")
                await asyncio.sleep(espera)
                busy = node_NewService.get_value()

        # Comprobar si la acción es realizable
        ok = self.servicePossible(node_AlmacenOcupacion, serviceType, int(target))
        if ok:
            # --------- Prod. Normal ------------
            # Escribir tipo de servicio solicitado
            # INTRODUCIR ( DejarCoger = 1 )
            if (serviceType == 'DELIVERY'):
                node_DejarCoger.set_attribute(ua.AttributeIds.Value, ua.DataValue(True))
            # EXTRAER ( DejarCoger = 0 )
            else:
                node_DejarCoger.set_attribute(ua.AttributeIds.Value, ua.DataValue(False))
            print("[" + self.myAgent.id + "] [AssetCommBehaviour, SendDataOPCUA] set operation " + serviceType + " in PLC")

            # Escribir posición objetivo de la solicitud
            node_Posicion.set_attribute(ua.AttributeIds.Value, ua.DataValue(ua.Variant(int(target), ua.VariantType.Int16)))
            print("[" + self.myAgent.id + "] [AssetCommBehaviour, SendDataOPCUA] set position " + str(target) + " in PLC")

            # Simular pulso de Reset
            node_Reset.set_attribute(ua.AttributeIds.Value, ua.DataValue(True))
            node_Reset.set_attribute(ua.AttributeIds.Value, ua.DataValue(False))
            print("[" + self.myAgent.id + "] [AssetCommBehaviour, SendDataOPCUA] action started in PLC")

            # Crear una variable que notifica del estado del proceso.
            # Cuando haya terminado la tarea, se pondrá en True
            finished = node_ServiceFinished.get_value()
            while not finished:
                await asyncio.sleep(1)
                finished = node_ServiceFinished.get_value()
            print("[" + self.myAgent.id + "] [AssetCommBehaviour, SendDataOPCUA] action finished in PLC")

            self.myAgent.client.close_session()

            # Devolver señal de tarea FINALIZADA
            return "FINISHED"

        else:
            self.myAgent.client.close_session()

            # Devolver señal de ERROR
            return "ERROR"

    def servicePossible(self, node_AlmacenOcupacion, service, target):
    # Este método permite saber si la operación solicitada puede realizarse
    # o si existe algún problema que no permita su puesta en marcha.

        # Obtener matriz de ocupación del almacén
        warehouseOcupation = node_AlmacenOcupacion.get_value()

        # Si se quiere INTRODUCIR Y la posición está ocupada
        if (service == 'DELIVERY' and warehouseOcupation[target - 1] == True):
            return False
        # Si se quiere EXTRAER Y la posición está vacía
        if (service == 'COLLECTION' and warehouseOcupation[target - 1] == False):
            return False

        return True
