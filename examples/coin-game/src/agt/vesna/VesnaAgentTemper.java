package vesna;

import jason.JasonException;
import jason.asSemantics.*;
import jason.asSyntax.*;
import jason.runtime.RuntimeServicesFactory;

import static jason.asSyntax.ASSyntax.*;

import java.net.URI;

import org.gradle.internal.impldep.org.apache.commons.lang.StringUtils;
import org.json.JSONObject;

import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.Random;

// VesnaAgent class extends the Agent class making the agent embodied;
// It connects to the body using a WebSocket connection;
// It needs two beliefs: address( ADDRESS ) and port( PORT ) that describe the address and port of the WebSocket server;
// In order to use it you should add to your .jcm:
// > agent alice:alice.asl {
// >      beliefs: address( localhost )
// >               port( 8080 )
// >      ag-class: vesna.VesnaAgent    
// > }

public class VesnaAgentTemper extends Agent{

	private WsClient client;
	private String my_name;
	private Map<String, Integer> propensions;

	// Override loadInitialAS method to connect to the WebSocket server (body)
	@Override
	public void loadInitialAS( String asSrc ) throws Exception {

		super.loadInitialAS( asSrc );
		my_name = getTS().getAgArch().getAgName();

		// Get the address from beliefs
		Unifier address_unifier = new Unifier();
		believes( parseLiteral( "address( Address )" ), address_unifier );

		// Get the port from beliefs
		Unifier port_unifier = new Unifier();
		believes( parseLiteral( "port( Port )" ), port_unifier );

		// Check if the address and port beliefs are defined
		if ( address_unifier.get( "Address" ) == null || port_unifier.get( "Port" ) == null ) {
				stop( "address and port beliefs are not defined!" );
				return;
		}

		// Store address and port in variables and initialize the WebSocket client
		String address = address_unifier.get( "Address" ).toString();
		int port = ( int ) ( ( NumberTerm ) port_unifier.get( "Port" ) ).solve();

		System.out.printf( "[%s] Body is at %s:%d%n", my_name, address, port );

		URI body_address = new URI( "ws://" + address + ":" + port );
		client = new WsClient( body_address );

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

		Unifier propension_unifier = new Unifier();

		if ( believes( createLiteral( "propensions", new VarTerm( "X" ) ), propension_unifier ) ){
			propensions = new HashMap<>();
			ListTerm propension_list = ( ListTerm) propension_unifier.get( "X" );
			for ( Term t : propension_list ) {
				Atom t_atom = ( Atom ) t;
				propensions.put( t_atom.getFunctor(), (int) ( ( NumberTerm )( t_atom.getTerm( 0 ) ) ).solve() );
			}
		}

		// Connect the body
		client.connect();
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
		if ( options.size() == 1 || !areOptionsWithPropension( options ) ) 
			return super.selectOption( options );
		Unifier u = new Unifier();
		if ( believes( createLiteral( "opt_choice", new VarTerm( "Choice" ) ), u ) ) {
            Literal temper = ( Literal ) u.get( "Choice" );
		    return select_option_with_temper( temper, options );
		}
        return super.selectOption( options );
	}

	private Option select_option_with_temper( Literal opt_choice, List<Option> options ) {
		double total_weight = 0.0;
		List<Integer> weights = new ArrayList<>();
        System.out.println( "Selecting option with modality: " + opt_choice.toString() );

		for ( Option opt : options ) {
			int opt_weight = 0;
			Pred l = opt.getPlan().getLabel();
			Literal prop_lit = createLiteral( "propensions", new VarTerm( "X" ) );

			Literal prop_annotation = l.getAnnot( "propensions" );
			if ( prop_annotation == null )
				continue;
			ListTerm opt_props = ( ListTerm) prop_annotation.getTerm( 0 );
			for ( Term p : opt_props ) {
				Atom a = ( Atom ) p;
				if ( ! propensions.keySet().contains( a.getFunctor() ) ) 
					continue;
                try {
                    int my_p = propensions.get( a.getFunctor() );
                    int plan_p = ( int ) ( ( NumberTerm ) a.getTerm( 0 ) ).solve();
                    if ( opt_choice.equals( createLiteral( "random") ) )
                        opt_weight += my_p * plan_p;
                    else if ( opt_choice.equals( createLiteral ( "most_similar" ) ) )
                        opt_weight += Math.abs( my_p - plan_p );
                } catch ( Exception e ) {
                    e.printStackTrace();
                }
			}
			weights.add( opt_weight );
		}
        if ( opt_choice.equals( createLiteral( "random" ) ) )
		    return options.get( get_weigthed_random_idx( weights ) );
        if ( opt_choice.equals( createLiteral( "most_similar" ) ) )
            return options.get( get_most_similar_idx( weights ) );
        return options.get( 0 );        
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
