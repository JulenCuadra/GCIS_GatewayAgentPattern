package agents;

import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import jade.core.AID;
import jade.core.Agent;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;
import jade.lang.acl.MessageTemplate;

import java.util.HashMap;
import java.util.Scanner;

public class Operator_Agent extends Agent {

    @Override
    protected void setup() {
        // When this method is called the agent has been already registered with the Agent Platform AMS and is able to send and receive messages.
        // However, the agent execution model is still sequential and no behaviour scheduling is active yet.
        // This method can be used for ordinary startup tasks such as DF registration, but is essential to add at least a Behaviour object to the agent.

        addBehaviour(new CyclicBehaviour() {

            String assetName;
            String service;
            String parameters;
            String msgContent;
            HashMap msgHashMap = new HashMap();

            Boolean enter_data = true;

            public void action() {
                if(enter_data){
                    // Introduzco el nombre del asset
                    Scanner in = new Scanner(System.in);
                    System.out.print("Please, introduce the name of the asset you want to request a service: ");
                    assetName = in.nextLine();

                    // Añado la información de la máquina órden y el lote
                    msgHashMap.put("Id_Machine_Reference","1");
                    msgHashMap.put("Id_Order_Reference","1");
                    msgHashMap.put("Id_Batch_Reference","1");

                    // Introduzco el nombre de un servicio
                    System.out.print("Please, introduce the number of the service you want to invoke (1/2/3): ");
                    service = in.nextLine();
                    msgHashMap.put("Operation_Ref_Service_Type",service);

                    // Introduzco el número de piezas que quiero fabricar
                    System.out.print("How many pieces do you require? (1/6): ");
                    parameters = in.nextLine();
                    msgHashMap.put("Operation_No_of_Items",parameters);

                    // Preparo el mensaje y se lo envío al agente asociado a ese asset
                    msgContent = new Gson().toJson(msgHashMap);
                    ACLMessage request = new ACLMessage(ACLMessage.REQUEST);
                    AID Factory_IO_Agent = new AID(assetName, false);
                    request.addReceiver(Factory_IO_Agent);
                    request.setOntology("data");
                    request.setContent(msgContent);
                    send(request);
                    enter_data = false;
                }

//                //Recibo la respuesta y la imprimo
                ACLMessage response = receive(MessageTemplate.MatchPerformative(ACLMessage.INFORM));
                if (response != null){

                    // Obtener el número del ítem producido
                    JsonObject json = new JsonParser().parse(response.getContent()).getAsJsonObject();
                    JsonObject item = (JsonObject) json.get("Id_Item_Number");
                    JsonObject machineReference = (JsonObject) json.get("Id_Machine_Reference");
                    JsonObject orderReference = (JsonObject) json.get("Id_Order_Reference");
                    JsonObject batchReference = (JsonObject) json.get("Id_Batch_Reference");
                    JsonObject serviceType = (JsonObject) json.get("Id_Ref_Service_Type");
                    JsonElement initialData = json.get("Data_Initial_Time_Stamp");
                    JsonElement finalData = (JsonElement) json.get("Data_Final_Time_Stamp");


                    System.out.println("Results from service requested to "+response.getSender().getLocalName()+": ");
                    //System.out.println(response.getContent()+"\n");

                    System.out.println("-------------------");
                    System.out.println(" *  ITEM NUMBER " + item.get("value") + "  *");
                    System.out.println("     - Id_Machine_Reference: " + machineReference.get("value"));
                    System.out.println("     - Id_Order_Reference: " + orderReference.get("value"));
                    System.out.println("     - Id_Batch_Reference: " + batchReference.get("value"));
                    System.out.println("     - Id_Ref_Service_Type: " + serviceType.get("value"));
                    System.out.println("     - Data_Initial_Time_Stamp: " + initialData.toString());
                    System.out.println("     - Data_Final_Time_Stamp: " + finalData.toString());
                    System.out.println();

                    // Compobar si se ha terminado el servicio
                    if(item.get("value").getAsInt() == Integer.parseInt(parameters)){
                        enter_data = true;
                    }
                }
            }
        });
    }

    @Override
    protected void takeDown() {
        // When this method is called the agent has not deregistered itself with the Agent Platform AMS and is still able to exchange messages with other agents.
        // However, no behaviour scheduling is active anymore and the Agent Platform Life Cycle state is already set to deleted.
        // This method can be used for ordinary cleanup tasks such as DF deregistration, but explicit removal of all agent behaviours is not needed.
        System.out.println("##### takeDown() #####");
    }
}
