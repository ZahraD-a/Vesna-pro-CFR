package vesna;

public interface WsClientMsgHandler {
    
    public void handle_msg( String msg );
    public void handle_error( Exception ex );
}
