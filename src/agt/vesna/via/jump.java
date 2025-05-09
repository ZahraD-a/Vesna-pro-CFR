package vesna;

import jason.asSemantics.*;
import jason.asSyntax.*;

import org.json.JSONObject;
import java.util.Set;

public class jump extends DefaultInternalAction {
   
    // jump     make a jump

    @Override
    public Object execute( TransitionSystem ts, Unifier un, Term[] args ) throws Exception {

        JSONObject data = new JSONObject();

        JSONObject action = new JSONObject();
        action.put( "sender", ts.getAgArch().getAgName() );
        action.put( "receiver", "body" );
        action.put( "type", "jump" );
        action.put( "data", data );

        return true;
    }
}
