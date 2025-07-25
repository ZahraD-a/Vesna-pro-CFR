package vesna;

import jason.JasonException;
import jason.architecture.AgArch;
import jason.asSemantics.*;
import jason.asSyntax.*;
import jason.runtime.RuntimeServicesFactory;
import jason.mas2j.ClassParameters;
import jason.bb.BeliefBase;
import jason.bb.DefaultBeliefBase;
import jason.runtime.Settings;

import static jason.asSyntax.ASSyntax.*;

import java.net.URI;

import org.gradle.internal.impldep.org.apache.commons.lang.StringUtils;
import org.json.JSONObject;

import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.Random;

import javax.validation.OverridesAttribute;

// VesnaAgent class extends the Agent class making the agent embodied;
// It connects to the body using a WebSocket connection;
// It can use four parameters:
// - address( ADDRESS ) and port( PORT ) that describe the address and port of the WebSocket server;
// - propensions( [ LIST OF PROPENSIONS ] ) and opt_choice( most_similar | random ) for the plan temper choice.
//
// In order to use it you should add to your .jcm:
// > agent alice:alice.asl {
// >	ag-class: 		vesna.VesnaAgent
// >	address: 		localhost
// >	port: 			8080
// >	propensions:	propensions([ ... ])
// >	opt_choice: 	random
// > }

public class VesnaAgent extends Agent{

	private WsClient client;
	private String my_name;
	private Map<String, Integer> propensions;
	private Map<String, Integer> dyn_propensions;
	private enum OptChoice { MOST_SIMILAR, RANDOM };
	private OptChoice optChoice;

	// Override loadInitialAS method to connect to the WebSocket server (body)
	// @Override
	// public void loadInitialAS( String asSrc ) throws Exception {
	public void initAg() {

		super.initAg();

		my_name = getTS().getAgArch().getAgName();
		Settings stts = getTS().getSettings();
		String prop_string = stts.getUserParameter( "propensions" );
		String opt_choice = stts.getUserParameter( "opt_choice" );
		String address = stts.getUserParameter( "address" );
		int port = Integer.parseInt( stts.getUserParameter( "port" ) );

		System.out.printf( "[%s] Body is at %s:%d%n", my_name, address, port );

		try {
			URI body_address = new URI( "ws://" + address + ":" + port );
			client = new WsClient( body_address );
		} catch( Exception e ){
			stop( e.getMessage() );
		}

		// Connect the two handle functions to the client object
		client.setMsgHandler( new WsClientMsgHandler() {
			@Override
			public void handle_msg( String msg ) {
				vesna_handle_msg( msg );
			}

			@Override
			public void handle_error( Exception ex ) {
				vesna_handle_error( ex );
			}
		}  );

		if ( prop_string != null ) {
		    propensions = new HashMap<>();
		    Literal prop_lit = Literal.parseLiteral( prop_string );
			List<Term> terms = prop_lit.getTerms();
			for ( Term t : terms ) {
			    Literal lit = ( Literal ) t;
				try {
					int value = ( int ) ( ( NumberTerm ) lit.getTerm( 0 ) ).solve();
				    propensions.put( lit.getFunctor().toString(), value );
				} catch( Exception e ) {
					stop( e.getMessage() );
				}
			}
		}
		dyn_propensions = new HashMap<>(propensions);

		if ( opt_choice.equals( "most_similar" ) )
			optChoice = OptChoice.MOST_SIMILAR;
		else if ( opt_choice.equals( "random" ) )
			optChoice = OptChoice.RANDOM;
		else
			stop( "The option choice is not valid" );

		// Connect the body
		try {
			client.connect();
		} catch( Exception e ){
			stop( e.getMessage() );
		}
	}

	// perform sends an action to the body
	public void perform( String action ) {
		client.send( action );
	}

	// sense signals the mind about a perception
	private void sense( Literal perception ) {
		try {
			Message signal = new Message( "signal", my_name, my_name , perception );
			getTS().getAgArch().sendMsg( signal );
		} catch ( Exception e ) {
			e.printStackTrace();
		}
	}

	// handle_event takes all the data from an event and senses a perception
	private void handle_event( JSONObject event ) {
		String event_type = event.getString( "type" );
		String event_status = event.getString( "status" );
		String event_reason = event.getString( "reason" );
		Literal perception = createLiteral( event_type, createLiteral( event_status ), createLiteral( event_reason ) );
		sense(perception);
	}

	// handle_sight takes all the data from a sight and adds a belief
	private void handle_sight( JSONObject sight ) {
		String object = sight.getString( "sight" );
		long id = sight.getLong( "id" );
		Literal sight_belief = createLiteral( "sight", createLiteral( object ), createNumber( id ) );
		try{
			addBel( sight_belief );
		} catch ( Exception e ) {
			e.printStackTrace();
		}
	}

	// this function handles incoming messages from the body
	// available types are: signal, sight
	public void vesna_handle_msg( String msg ) {
		System.out.println( "Received message: " + msg );
		JSONObject log = new JSONObject( msg );
		String sender = log.getString( "sender" );
		String receiver = log.getString( "receiver" );
		String type = log.getString( "type" );
		JSONObject data = log.getJSONObject( "data" );
		switch( type ){
			case "signal":
				handle_event( data );
				break;
			case "sight":
				handle_sight( data );
				break;
			default:
				System.out.println( "Unknown message type: " + type );
		}
	}

	// Stops the agent: prints a message and kills the agent
	private void stop( String reason ) {
		System.out.println( "[" + my_name + " ERROR] " + reason );
		kill_agent();
	}

	// Handles a connection error: prints a message and kills the agent
	public void vesna_handle_error( Exception ex ){
		System.out.println( "[" + my_name + " ERROR] " + ex.getMessage() );
		kill_agent();
	}

	// Kills the agent calling the internal actions to drop all desires, intentions and events and then kill the agent;
	// This is necessary to avoid the agent to keep running after the kill_agent call ( that otherwise is simply enqueued ).
	private void kill_agent() {
		System.out.println( "[" + my_name + " ERROR] Killing agent" );
		try {
			InternalAction drop_all_desires = getIA( ".drop_all_desires" );
			InternalAction drop_all_intentions = getIA( ".drop_all_intentions" );
			InternalAction drop_all_events = getIA( ".drop_all_events" );
			InternalAction action = getIA( ".kill_agent" );

			drop_all_desires.execute( getTS(), new Unifier(), new Term[] {} );
			drop_all_intentions.execute( getTS(), new Unifier(), new Term[] {} );
			drop_all_events.execute( getTS(), new Unifier(), new Term[] {} );
			action.execute( getTS(), new Unifier(), new Term[] { createString( my_name ) } );
		} catch ( Exception e ) {
			e.printStackTrace();
		}
	}

	public Option selectOption( List<Option> options ) {
		if ( options.size() == 1 || !areOptionsWithPropension( options ) ) {
			return super.selectOption( options );
		}
		if ( optChoice != null )
		    return select_option_with_temper( options );
        return super.selectOption( options );
	}

	private Option select_option_with_temper( List<Option> options ) {
		double total_weight = 0.0;
		List<Integer> weights = new ArrayList<>();
		System.out.println( "Dynamic temper: " + dyn_propensions );

		for ( Option opt : options ) {
			int opt_weight = 0;
			Pred l = opt.getPlan().getLabel();

			Literal prop_annotation = l.getAnnot( "propensions" );
			if ( prop_annotation == null )
				continue;
			ListTerm opt_props = ( ListTerm) prop_annotation.getTerm( 0 );
			for ( Term p : opt_props ) {
				Atom a = ( Atom ) p;
				if ( ! dyn_propensions.keySet().contains( a.getFunctor() ) )
					continue;
                try {
                    int my_p = dyn_propensions.get( a.getFunctor() );
                    int plan_p = ( int ) ( ( NumberTerm ) a.getTerm( 0 ) ).solve();
                    if ( optChoice == OptChoice.RANDOM )
                        opt_weight += my_p * plan_p;
                    else if ( optChoice == OptChoice.MOST_SIMILAR )
                        opt_weight += Math.abs( my_p - plan_p );
                } catch ( Exception e ) {
                    e.printStackTrace();
                }
			}
			weights.add( opt_weight );
		}
		Option chosen = options.get( 0 );
        if ( optChoice == OptChoice.RANDOM )
		    chosen = options.get( get_weigthed_random_idx( weights ) );
        if ( optChoice == OptChoice.MOST_SIMILAR )
            chosen = options.get( get_most_similar_idx( weights ) );
        Literal effectList = chosen.getPlan().getLabel().getAnnot( "effects" );
        if ( effectList != null )
        	update_dyn_propensions(effectList);
        return chosen;
	}

	private void update_dyn_propensions( Literal effectList ) {
		ListTerm effects = (ListTerm) effectList.getTerm( 0 );
		for ( Term t : effects ) {
			Literal l = ( Literal ) t;
			if ( dyn_propensions.get( l.getFunctor().toString() ) != null ) {
				try{
					int curr_value = dyn_propensions.get( l.getFunctor().toString() );
					int effect = ( int ) ( (NumberTerm) l.getTerm( 0 ) ).solve();
					dyn_propensions.put( l.getFunctor().toString(), curr_value + effect );
				} catch ( Exception e ) {
					System.err.println("Error updating dynamic propensions: " + e.getMessage());
				}
			}
		}
	}

	private boolean areOptionsWithPropension( List<Option> options ) {
		Literal propension = createLiteral( "propensions", new VarTerm( "X" ) );
		for ( Option option : options ) {
			Plan p = option.getPlan();
			Pred l = p.getLabel();
			if ( l.hasAnnot() ) {
				for ( Term t : l.getAnnots() )
					if ( new Unifier().unifies( propension, t ) )
						return true;
			}
		}
		return false;
	}

	private int get_weigthed_random_idx( List<Integer> weights ) {
		int sum = weights.stream().reduce( 0, Integer::sum );
		Random dice = new Random();
		int roll = dice.nextInt( sum );
		int cur_min = 0;
		for ( int i = 0; i < weights.size(); i++ ) {
			if ( roll > cur_min && roll < weights.get( i ) + cur_min )
				return i;
			cur_min += weights.get( i );
		}
		return 0;
	}

	private int get_most_similar_idx( List<Integer> weights ) {
        int min = Integer.MAX_VALUE;
        int min_idx = -1;
        for ( int i = 0; i < weights.size(); i++ ) {
            if ( weights.get( i ) < min ) {
                min = weights.get( i );
                min_idx = i;
            }
        }
        return min_idx;
	}

}
