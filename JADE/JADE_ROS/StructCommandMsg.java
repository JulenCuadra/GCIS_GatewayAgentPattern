package com.github.rosjava.fms_transp.turtlebot2;

public class StructCommandMsg {

    private String action;
    private java.lang.Object content;

    public StructCommandMsg() {}

    public void setAction (String _action) { this.action = _action; }
    public void setContent (java.lang.Object _content) { this.content = _content; }

    public String getAction () { return this.action; }
    public java.lang.Object getContent () { return this.content; }

}
