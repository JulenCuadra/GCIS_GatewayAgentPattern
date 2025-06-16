package com.github.rosjava.fms_transp.turtlebot2;

import jade.core.AID;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;
import jade.lang.acl.MessageTemplate;
import jade.wrapper.gateway.GatewayAgent;

import com.google.gson.Gson;

import com.github.rosjava.fms_transp.turtlebot2.StructCommandMsg;
import com.github.rosjava.fms_transp.turtlebot2.StructTranspState;

public class GWagentROSmsg extends GatewayAgent {

    private String JSONmsg_content = null;

    @Override
    protected void processCommand(java.lang.Object _command) {
        StructCommandMsg command = (StructCommandMsg) _command;
        String action = command.getAction();

        if(action.equals("init")) {
            System.out.println("--- GWagentROS init() command called.");
            System.out.println("--- Hi, I am a Gateway Agent!");

        } else if(action.equals("recv")) {
            if(JSONmsg_content != null) {
                System.out.println("--- The Gateway Agent is returning the message.");

                Gson gson = new Gson();
                StructTranspState javaTranspState = gson.fromJson(JSONmsg_content, StructTranspState.class);
                ((StructCommandMsg) command).setContent(javaTranspState);

                JSONmsg_content = null;
            } else {
                System.out.println("--- The Gateway Agent has no message to return.");
            }
        }

        releaseCommand(command);
    }

    @Override
    public void setup() {
        super.setup();

        MessageTemplate matchPerformative = MessageTemplate.or(MessageTemplate.MatchPerformative(ACLMessage.REQUEST),MessageTemplate.MatchPerformative(ACLMessage.INFORM));
        MessageTemplate matchOntology = MessageTemplate.MatchOntology("data");
        MessageTemplate matchConversationID = MessageTemplate.MatchConversationId("1234");
        final MessageTemplate messageTemplate =  MessageTemplate.and(MessageTemplate.and(matchPerformative, matchOntology), matchConversationID);

        addBehaviour(new CyclicBehaviour() {
            public void action() {
                ACLMessage msg = receive(messageTemplate);
                if(msg != null) {
                    System.out.println("--- The Gateway Agent has received a message from TA!");
                    JSONmsg_content = msg.getContent();
                } else {
                    System.out.println("--- No messages from TA. The Gateway Agent is blocking.");
                    block();
                }
            }
        });
    }
}



