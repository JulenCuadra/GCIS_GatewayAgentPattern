package agents.gateway;

import utilities.StructMessage;
import jade.core.AID;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;
import jade.lang.acl.MessageTemplate;
import jade.wrapper.gateway.GatewayAgent;

public class GWAgentOPCUA extends GatewayAgent {

    public String msgRecv;
    public AID machineAgentName;

    @Override
    protected void processCommand(Object _command) {

        // Se comprueba si el objeto recibido es del tipo esperado
        if(!(_command instanceof StructMessage)){
            System.out.println("---Error, unexpected type");
            releaseCommand(_command);
        }

        // Se procesa la estructura recibida al invocar el agente y se lee la acci�n a realizar
        StructMessage command = (StructMessage) _command;
        String action = command.readAction();

        switch (action) {

            case "init":

                // Se printea un mensaje por pantalla
                System.out.println("--- GWagentOPCUA init() command called.");
                break;
            case "receive":

                // Se comprueba si se ha recibido alg�n mensaje
                if (msgRecv != null) {

                    //En caso afirmativo, se guarda en la estructura de datos
                    command.setMessage(msgRecv);
                    msgRecv = null;
                }
                break;
            case "send":

                // Se declara un nuevo mensaje ACL con la performativa y el contenido recibidos en la estructura
                // Tambi�n se definen el receptor (el agente que me escribi� primero)
                // La ontolog�a tambi�n se define, pero dependiendo del contenido del mensaje (asset_state o assetdata)
                ACLMessage msgToAgent = new ACLMessage(ACLMessage.INFORM);
                msgToAgent.addReceiver(machineAgentName);
                msgToAgent.setOntology("assetdata");
                msgToAgent.setContent(command.readMessage());
                send(msgToAgent);
                break;
        }

        // Se ejecuta el m�todo releaseCommand para finalizar la ejecuci�n
        releaseCommand(command);
    }

    @Override
    public void setup() {

        super.setup();

        // Se definen tres templates: uno para el ping (se comprueba si el gatewayAgent est� vivo)
        MessageTemplate templatePing = MessageTemplate.and(
                MessageTemplate.MatchPerformative(ACLMessage.REQUEST),MessageTemplate.MatchOntology("ping"));

        // Un segundo template para comprobar el estado del asset
        MessageTemplate templateCheckAsset = MessageTemplate.and(
                MessageTemplate.MatchPerformative(ACLMessage.REQUEST),MessageTemplate.MatchOntology("check_asset"));

        // Y un tercero para el intercambio normal de mensajes
        MessageTemplate templateWork = MessageTemplate.and(
                MessageTemplate.MatchPerformative(ACLMessage.REQUEST),MessageTemplate.MatchOntology("data"));

        addBehaviour(new CyclicBehaviour() {

            public void action() {

                // Se procesa cualquier mensaje
                ACLMessage msg = receive();

                // Se comprueba si se ha recibido alg�n mensaje o no
                if (msg != null){

                    // Si hay mensaje, se establecen las acciones a realizar dependiendo del tipo de mensaje
                    if (templatePing.match(msg)){

                        // Si se ha recibido un mensaje de este tipo, se responde al ping
                        ACLMessage reply = new ACLMessage(ACLMessage.INFORM);
                        reply.addReceiver(msg.getSender());
                        reply.setOntology(msg.getOntology());
                        reply.setContent("Alive");
                        System.out.println(msg.getSender().getLocalName()+" sent a ping. Answering.");
                        send(reply);

                    } else if (templateCheckAsset.match(msg)){

                        // Si se ha recibido un mensaje de este tipo, se guarda el contenido del mensaje
                        // Tambi�n se guarda el AID del solicitante
                        msgRecv = msg.getContent();
                        machineAgentName = msg.getSender();

                    } else if (templateWork.match(msg)){

                        // Si se ha recibido un mensaje de este tipo, se responde con un acknowledge
                        ACLMessage ack=new ACLMessage(ACLMessage.CONFIRM);
                        ack.setOntology(msg.getOntology());
                        ack.setConversationId(msg.getConversationId());
                        ack.setContent(msg.getContent());
                        ack.addReceiver(msg.getSender());
                        send(ack);

                        // Adem�s, se guardan el contenido del mensaje y el AID de la m�quina
                        msgRecv=msg.getContent();
                        machineAgentName = msg.getSender();

                    }

                } else { // Si no hay mensaje, se bloquea el agente

                    block();
                }
            }
        });
    }
}
