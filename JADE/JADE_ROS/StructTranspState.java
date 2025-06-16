package com.github.rosjava.fms_transp.turtlebot2;

public class StructTranspState {

    private int entero;
    private String cadena;

    public StructTranspState() {}

    public void setEntero (int _entero) { this.entero = _entero; }
    public void setCadena (String _cadena) { this.cadena = _cadena; }

    public int getEntero () { return this.entero; }
    public String getCadena () { return this.cadena; }

}
