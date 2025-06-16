package agents.gateway;

import com.google.gson.Gson;
import org.eclipse.milo.opcua.sdk.client.OpcUaClient;
import org.eclipse.milo.opcua.sdk.client.api.AddressSpace;
import org.eclipse.milo.opcua.sdk.client.api.config.OpcUaClientConfigBuilder;
import org.eclipse.milo.opcua.sdk.client.api.nodes.VariableNode;
import org.eclipse.milo.opcua.stack.client.UaTcpStackClient;
import org.eclipse.milo.opcua.stack.core.types.builtin.DataValue;
import org.eclipse.milo.opcua.stack.core.types.builtin.NodeId;
import org.eclipse.milo.opcua.stack.core.types.builtin.StatusCode;
import org.eclipse.milo.opcua.stack.core.types.builtin.Variant;
import org.eclipse.milo.opcua.stack.core.types.builtin.unsigned.UByte;
import org.eclipse.milo.opcua.stack.core.types.builtin.unsigned.UInteger;
import org.eclipse.milo.opcua.stack.core.types.structured.EndpointDescription;
import utilities.StructMessage;
import jade.core.Profile;
import jade.util.leap.Properties;
import jade.wrapper.ControllerException;
import jade.wrapper.gateway.JadeGateway;

import java.net.Inet4Address;
import java.net.InetAddress;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class ACL_OPCUA_Gateway {

    // Declaración de variables
    OpcUaClient client;

    public ACL_OPCUA_Gateway(String[] args) {

        //Antes de empezar, las presentaciones (portada para el usuario)
        System.out.println("This is a Java Class acting as a gateway between ACL (IARMS4.0 Agents) and OPCUA (Factory I/O Demonstrator).\n");

        //Primero se establece conexión con el servidor OPC UA y se inicializa el gatewayAgent
        try {
            this.OPCUA_Connect();
            this.jadeInit(args);
        } catch (Exception e) {
            e.printStackTrace();
        }

        //Después habrá que declarar el while para mantener el hilo en marcha
        while (true){

            // Dentro del while, se comprobará constantemente si se han recibido mensajes en el gatewayAgent
            String request = null;
            try {
               request = jadeReceive();
            } catch (ControllerException | InterruptedException e) {
                e.printStackTrace();
            }

            if (request != null) { // Si se ha recibido un mensaje, se procesa el servicio

                try {
                    processService_OPCUA(request);
                } catch (ExecutionException | InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    private void OPCUA_Connect () throws ExecutionException, InterruptedException {

        //Se establece conexión con el servidor OPC UA
        final String endpointUrl = "opc.tcp://192.168.5.11:4840";
        final EndpointDescription[] endpoints = UaTcpStackClient.getEndpoints(endpointUrl).get();
        final OpcUaClientConfigBuilder config = new OpcUaClientConfigBuilder();
        config.setEndpoint(endpoints[0]);

        client = new OpcUaClient(config.build());
        client.connect().get();
    }

    private void jadeInit(String[] args) throws Exception {

        //Primero, se leen los argumentos recibidos en la invocación de la clase
        String assetName = args[0];
        String host = args[1];

        //A continuación, se definen el resto de parámetros que van a hacer falta para crear el gatewayAgent
        String localHostName = InetAddress.getLocalHost().getHostName();
        InetAddress[] addressses = InetAddress.getAllByName(localHostName);
        String port = "1099";
        String containerName = "GatewayCont"+assetName;

        //Se declara un bucle para iterar sobre todas las IPs que se han obtenido en el array addresses[]
        for (InetAddress addresss : addressses) {
            if (addresss instanceof Inet4Address) {

                String[] localHost = String.valueOf(addresss).split("/");

                //Se definen las propiedades que caracterizan al contenedor del GatewayAgent:  puerto y nombre del contenedor
                Properties pp = new Properties();
                pp.setProperty(Profile.LOCAL_HOST, localHost[localHost.length - 1]); //Dirección IP del gatewayAgent
                pp.setProperty(Profile.MAIN_HOST, host); //Dirección IP de la plataforma de agentes (JADE)
                pp.setProperty(Profile.MAIN_PORT, port); //Puerto de acceso del gatewayAgent
                pp.setProperty(Profile.LOCAL_PORT, port); //Puerto de acceso de la plataforma de agentes (JADE)
                pp.setProperty(Profile.CONTAINER_NAME, containerName); //Nombre del contenedor

                //Se inicializa el GatewayAgent de la clase correspondiente
                JadeGateway.init("agents.gateway.GWAgentOPCUA", pp);

                //Se ejecuta el comando init para garantizar el arranque del GatewayAgent
                StructMessage strMessage = new StructMessage();
                strMessage.setAction("init");
                try {
                    JadeGateway.execute(strMessage);
                    break;
                } catch (ControllerException | InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    private String jadeReceive() throws ControllerException, InterruptedException {

            //Se invoca la acción receive del GatewayAgent para recibir posibles mensajes
            StructMessage strMessage = new StructMessage();
            strMessage.setAction("receive");
            JadeGateway.execute(strMessage);

            //Se comprueba si hay un nuevo mensaje
            String msgFromGW;
            if (strMessage.readMessage() != null) { //En caso afirmativo, se lee el mensaje
                msgFromGW = strMessage.readMessage();
            } else { //En caso contrario, se devuelve null
                msgFromGW = null;
            }

            return msgFromGW;
    }

    private void jadeSend(String response) throws ControllerException, InterruptedException {

        //Se declara la estructura que se le va a pasar al GatewayAgent
        StructMessage strMessage = new StructMessage();

        //Se definen la acción (enviar) y el contenido (response)
        strMessage.setAction("send");
        strMessage.setMessage(response);

        //Por último, se envía el mensaje
        JadeGateway.execute(strMessage);
    }

    private void processService_OPCUA (String cmd) throws ExecutionException, InterruptedException {

        //Primero inicializo las variables que voy a necesitar
        HashMap<String,Object> requestHashMap;
        HashMap<String,Object> responseHashMap = new HashMap<String, Object>();
        Boolean Control_Flag_New_Service = true;
        Boolean Control_Flag_Item_Completed = false;
        Boolean Control_Flag_Service_Completed = false;

        HashMap<String, NodeId> nodeId = new HashMap<String, NodeId>();

        // Control parameters
        nodeId.put("Control_Flag_New_Service", new NodeId(4,5));
        nodeId.put("Control_Flag_Item_Completed", new NodeId(4,6));
        nodeId.put("Control_Flag_Service_Completed", new NodeId(4,7));

        // Data from Gateway Agent
        nodeId.put("Id_Machine_Reference_1", new NodeId(4,11));
        nodeId.put("Id_Order_Reference_1", new NodeId(4,12));
        nodeId.put("Id_Batch_Reference_1", new NodeId(4,13));
        nodeId.put("Operation_Ref_Service_Type", new NodeId(4,14));
        nodeId.put("Operation_No_of_Items", new NodeId(4,15));

        // Data to Gateway Agent
        nodeId.put("Id_Machine_Reference_2", new NodeId(4,19));
        nodeId.put("Id_Order_Reference_2", new NodeId(4,20));
        nodeId.put("Id_Batch_Reference_2", new NodeId(4,21));
        nodeId.put("Id_Ref_Service_Type", new NodeId(4,22));
        nodeId.put("Id_Item_Number", new NodeId(4,23));
        nodeId.put("Data_Initial_Time_Stamp", new NodeId(4,24));
        nodeId.put("Data_Final_Time_Stamp", new NodeId(4,25));

        // Después, transformo el mensaje recibido de vuelta en un HashMap
        requestHashMap = new Gson().fromJson(cmd, HashMap.class);

        // Se eliminan los decimales de los valores numéricos
        for(Map.Entry<String,Object> item : requestHashMap.entrySet()){
            if (item.getValue() instanceof Double){
                requestHashMap.put(item.getKey(), String.valueOf(Math.round((Double) item.getValue())));
            }
        }


        //      ******     Send the order request     ******
        System.out.println("\n\n******     Send the order request     ******");

        // Set Id Machine Reference
        DataValue data = new DataValue(new Variant(UInteger.valueOf((String) requestHashMap.get("Id_Machine_Reference"))), StatusCode.GOOD, null);
        StatusCode status = client.writeValue(nodeId.get("Id_Machine_Reference_1"), data).get();
        System.out.println("-------------------");
        System.out.println("Id_Machine_Reference:\n     - Value: " + data.getValue().getValue() + "\n     - Good Status: " + status.isGood());

        // Set Id Order Reference
        data = new DataValue(new Variant(UInteger.valueOf((String) requestHashMap.get("Id_Order_Reference"))), StatusCode.GOOD, null);
        status = client.writeValue(nodeId.get("Id_Order_Reference_1"), data).get();
        System.out.println("-------------------");
        System.out.println("Id_Order_Reference:\n     - Value: " + data.getValue().getValue() + "\n     - Good Status: " + status.isGood());

        // Set Id Batch Reference
        data = new DataValue(new Variant(UInteger.valueOf((String) requestHashMap.get("Id_Batch_Reference"))), StatusCode.GOOD, null);
        status = client.writeValue(nodeId.get("Id_Batch_Reference_1"), data).get();
        System.out.println("-------------------");
        System.out.println("Id_Batch_Reference:\n     - Value: " + data.getValue().getValue() + "\n     - Good Status: " + status.isGood());

        // Set Operation Ref Service Type
        data = new DataValue(new Variant(UInteger.valueOf((String) requestHashMap.get("Operation_Ref_Service_Type"))), StatusCode.GOOD, null);
        status = client.writeValue(nodeId.get("Operation_Ref_Service_Type"), data).get();
        System.out.println("-------------------");
        System.out.println("Operation_Ref_Service_Type:\n     - Value: " + data.getValue().getValue() + "\n     - Good Status: " + status.isGood());

        // Set Operation No of Items
        data = new DataValue(new Variant(UInteger.valueOf((String) requestHashMap.get("Operation_No_of_Items"))), StatusCode.GOOD, null);
        status = client.writeValue(nodeId.get("Operation_No_of_Items"), data).get();
        System.out.println("-------------------");
        System.out.println("Operation_No_of_Items:\n     - Value: " + data.getValue().getValue() + "\n     - Good Status: " + status.isGood());

        // Activate New Service Flag
        data = new DataValue(new Variant(Control_Flag_New_Service), StatusCode.GOOD, null);
        status = client.writeValue(nodeId.get("Control_Flag_New_Service"), data).get();
        System.out.println("-------------------");
        System.out.println("Control_Flag_New_Service:\n     - Value: " + data.getValue().getValue() + "\n     - Good Status: " + status.isGood());


        //      ******     Get process data     ******
        System.out.println("\n\n******     Get process data     ******");
        AddressSpace addressSpace = client.getAddressSpace();
        do{
            // Check if the service is over
            CompletableFuture<VariableNode> node = addressSpace.getVariableNode(nodeId.get("Control_Flag_Service_Completed"));
            VariableNode testNode = node.get();
            CompletableFuture<DataValue> value = testNode.readValue();
            DataValue testValue = value.get();
            Control_Flag_Service_Completed = (Boolean) testValue.getValue().getValue();

            // Check if an item is finished
            node = addressSpace.getVariableNode(nodeId.get("Control_Flag_Item_Completed"));
            testNode = node.get();
            value = testNode.readValue();
            testValue = value.get();
            Control_Flag_Item_Completed = (Boolean) testValue.getValue().getValue();

            if(Control_Flag_Item_Completed){

                // Deactivate Item Completed Flag
                Control_Flag_Item_Completed = false;

                // Get Id Machine Reference
                node = addressSpace.getVariableNode(nodeId.get("Id_Machine_Reference_2"));
                testNode = node.get();
                value = testNode.readValue();
                testValue = value.get();
                responseHashMap.put("Id_Machine_Reference",(UInteger) testValue.getValue().getValue());

                // Get Id Order Reference
                node = addressSpace.getVariableNode(nodeId.get("Id_Order_Reference_2"));
                testNode = node.get();
                value = testNode.readValue();
                testValue = value.get();
                responseHashMap.put("Id_Order_Reference",(UInteger) testValue.getValue().getValue());

                // Get Id Batch Reference
                node = addressSpace.getVariableNode(nodeId.get("Id_Batch_Reference_2"));
                testNode = node.get();
                value = testNode.readValue();
                testValue = value.get();
                responseHashMap.put("Id_Batch_Reference",(UInteger) testValue.getValue().getValue());

                // Get Id Service Type
                node = addressSpace.getVariableNode(nodeId.get("Id_Ref_Service_Type"));
                testNode = node.get();
                value = testNode.readValue();
                testValue = value.get();
                responseHashMap.put("Id_Ref_Service_Type",(UInteger) testValue.getValue().getValue());

                // Get Id Item Number
                node = addressSpace.getVariableNode(nodeId.get("Id_Item_Number"));
                testNode = node.get();
                value = testNode.readValue();
                testValue = value.get();
                responseHashMap.put("Id_Item_Number",(UByte) testValue.getValue().getValue());

                // Get Data Initial Time Stamp
                node = addressSpace.getVariableNode(nodeId.get("Data_Initial_Time_Stamp"));
                testNode = node.get();
                value = testNode.readValue();
                testValue = value.get();
                responseHashMap.put("Data_Initial_Time_Stamp",(String) testValue.getValue().getValue());

                // Get Data Final Time Stamp
                node = addressSpace.getVariableNode(nodeId.get("Data_Final_Time_Stamp"));
                testNode = node.get();
                value = testNode.readValue();
                testValue = value.get();
                responseHashMap.put("Data_Final_Time_Stamp",(String) testValue.getValue().getValue());

                // Prepare the message with the results and send it to the Factory_IO_Agent using the jadeSend method
                String response = new Gson().toJson(responseHashMap);
                try {
                    jadeSend(response);
                } catch (ControllerException | InterruptedException e) {
                    e.printStackTrace();
                }

                // Update the status of Item Completed Flag
                data = new DataValue(new Variant(Control_Flag_Item_Completed), StatusCode.GOOD, null);
                status = client.writeValue(nodeId.get("Control_Flag_Item_Completed"), data).get();
                System.out.println("     -------------------");
                System.out.println("     Control_Flag_Item_Completed:\n          - Value: " + data.getValue().getValue() + "\n          - Good Status: " + status.isGood());
            }

            try {
                Thread.sleep (2000);
            } catch (Exception e) {
                System.out.println(e.getMessage());
            }
        } while (!Control_Flag_Service_Completed);

        System.out.println("\n\n******     THE SERVICE IS OVER     ******");

        // Deactivate Service Completed Flag
        Control_Flag_Service_Completed = false;

        // Update the status of Service Completed Flag
        data = new DataValue(new Variant(Control_Flag_Service_Completed), StatusCode.GOOD, null);
        status = client.writeValue(nodeId.get("Control_Flag_Service_Completed"), data).get();
        System.out.println("-------------------");
        System.out.println("Control_Flag_Service_Completed:\n     - Value: " + data.getValue().getValue() + "\n     - Good Status: " + status.isGood());
        client.disconnect().get();
    }

    public static void main(String[] args) {

        ACL_OPCUA_Gateway GW_ACL_OPCUA= new ACL_OPCUA_Gateway(args);
    }
}
