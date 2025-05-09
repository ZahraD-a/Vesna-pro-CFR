package vesna;

import jason.asSemantics.*;
import jason.asSyntax.*;

import org.json.JSONObject;
import java.util.Set;

public class rotate extends DefaultInternalAction {
   
    // rotate( left )       rotate in a direction
    // rotate( target )     look at target
    // rotate( target, id ) look at target with id

    Set directions = Set.of( "left", "right", "forward", "backward" );

    @Override
    public Object execute( TransitionSystem ts, Unifier un, Term[] args ) throws Exception {

        JSONObject data = new JSONObject();
        if ( args.length == 0 )
            return false;
        
        if ( directions.contains( args[0].toString() ) ){
            data.put( "type", "direction" );
            data.put( "direction", args[0].toString() );
        } else {
            data.put( "type", "lookat" );
            data.put( "target", args[0].toString() );
            if ( args.length == 2 )
                data.put( "id", ( ( NumberTerm ) args[1] ).solve() );
        }
        

        JSONObject action = new JSONObject();
        action.put( "sender", ts.getAgArch().getAgName() );
        action.put( "receiver", "body" );
        action.put( "type", "rotate" );
        action.put( "data", data );

        return true;
    }
}
