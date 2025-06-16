package com.github.rosjava.fms_transp.turtlebot2;

import java.net.URI;

import org.ros.message.Time;
import org.ros.namespace.GraphName;
import org.ros.node.AbstractNodeMain;
import org.ros.node.ConnectedNode;
import org.ros.node.DefaultNodeMainExecutor;
import org.ros.address.InetAddressFactory;
import org.ros.node.NodeConfiguration;
import org.ros.node.NodeMain;
import org.ros.node.NodeMainExecutor;
import org.ros.node.topic.Publisher;
import org.apache.commons.logging.Log;

import jade.core.Profile;
import jade.util.leap.Properties;
import jade.wrapper.gateway.JadeGateway;

import fms_msgs.transp_state;

import com.github.rosjava.fms_transp.turtlebot2.StructCommandMsg;
import com.github.rosjava.fms_transp.turtlebot2.StructTranspState;


public class NodePubMsgRunMainJadeGW extends AbstractNodeMain {

  public NodePubMsgRunMainJadeGW() {
    try {
      this.jadeInit();
      this.rosInit();
    } catch(Exception e) {
      System.out.println(e.getMessage());
    }
  }

  private void rosInit() throws Exception {
    String host = InetAddressFactory.newNonLoopback().getHostName();
    String port = "11311";
    String masterURI_str = "http://" + host + ":" + port;
    URI masterURI = new URI(masterURI_str);

    NodeConfiguration nodeConfiguration = NodeConfiguration.newPrivate();
    nodeConfiguration.setMasterUri(masterURI);
    nodeConfiguration.setNodeName("NodePubMsg");

    NodeMain nodeMain = (NodeMain) this;
    NodeMainExecutor nodeMainExecutor = DefaultNodeMainExecutor.newDefault();
    nodeMainExecutor.execute(nodeMain, nodeConfiguration);
  }

  private void jadeInit() throws Exception {
    Properties pp = new Properties();

    String host = InetAddressFactory.newNonLoopback().getHostName();
    String port = "1099";
    pp.setProperty(Profile.MAIN_HOST, host);
    pp.setProperty(Profile.MAIN_PORT, port);
    pp.setProperty(Profile.LOCAL_PORT, port);

    java.lang.String containerName = "GatewayContMsg1";
    pp.setProperty(Profile.CONTAINER_NAME, containerName);

    JadeGateway.init("com.github.rosjava.fms_transp.turtlebot2.GWagentROSmsg", pp);

    StructCommandMsg command = new StructCommandMsg();
    command.setAction("init");
    JadeGateway.execute(command);
  }

  @Override
  public GraphName getDefaultNodeName() {
    return GraphName.of("NodePubMsg");
  }

  @Override
  public void onStart(final ConnectedNode connectedNode) {
    Publisher<transp_state> publisher = connectedNode.newPublisher("coordinateMsg", transp_state._TYPE);
    final Log log = connectedNode.getLog();

    while(true) {
      StructCommandMsg command = new StructCommandMsg();
      command.setAction("recv");

      try {
        JadeGateway.execute(command);
      } catch(Exception e) {
        System.out.println(e.getMessage());
      }
      StructTranspState javaTranspState = (StructTranspState) command.getContent();

      if(javaTranspState != null) {
        int entero = javaTranspState.getEntero();
        String cadena = javaTranspState.getCadena();

        transp_state rosTranspState = publisher.newMessage();
        rosTranspState.getHeader().setStamp(Time.fromMillis(System.currentTimeMillis()));
        rosTranspState.setEntero((byte) entero);
        rosTranspState.setCadena(cadena);

        publisher.publish(rosTranspState);
        log.info("NodePub publishing in topic /coordinateMsg");
      } else {
        log.info("NodePub has no message to publish");
      }
    }
  }

  public static void main(String[] args) {
    NodePubMsgRunMainJadeGW nodePubObj = new NodePubMsgRunMainJadeGW();
  }

}

