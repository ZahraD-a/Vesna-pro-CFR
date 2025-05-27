package vesna;

import jason.asSemantics.*;
import jason.asSyntax.*;

import org.json.JSONObject;
import java.util.Set;

import static jason.asSyntax.ASSyntax.*;

public class jump extends DefaultInternalAction {
   
    // jump     make a jump

    @Override
    public Object execute( TransitionSystem ts, Unifier un, Term[] args ) throws Exception {

        JSONObject data = new JSONObject();
        JSONObject propensions = new JSONObject();

        VesnaAgent ag = ( VesnaAgent ) ts.getAg();
        Unifier u = new Unifier();
        if ( ag.believes( createLiteral( "propensions" , new VarTerm( "Ps" ) ), u ) ) {
            ListTerm props = ( ListTerm ) u.get( "Ps" );
        }

        JSONObject action = new JSONObject();
        action.put( "sender", ts.getAgArch().getAgName() );
        action.put( "receiver", "body" );
        action.put( "type", "jump" );
        action.put( "data", data );

        return true;
    }
}
