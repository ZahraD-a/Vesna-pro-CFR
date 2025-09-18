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
import jason.NoValueException;

import static jason.asSyntax.ASSyntax.*;

import java.net.URI;

import org.gradle.internal.impldep.org.apache.commons.lang.StringUtils;
import org.json.JSONObject;

import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.Random;
import java.util.Queue;
import java.util.Set;
import java.util.HashSet;
import java.util.Iterator;
import java.util.stream.Collectors;

import java.util.logging.Logger;

import javax.validation.OverridesAttribute;

// VesnaAgent class extends the Agent class making the agent embodied;
// It connects to the body using a WebSocket connection;
// It can use four parameters:
// - address( ADDRESS ) and port( PORT ) that describe the address and port of the WebSocket server;
// - temper( [ LIST OF PROPENSIONS ] ) and strategy( most_similar | random ) for the plan temper choice.
//
// In order to use it you should add to your .jcm:
// > agent alice:alice.asl {
// >	ag-class: 		vesna.VesnaAgent
// >	address: 		localhost
// >	port: 			8080
// >	temper:			propensions([ ... ])
// >	strategy: 		random
// > }

public class VesnaAgent extends Agent{

	// GLOBAL VARIABLES
	private WsClient client;
	private String myName;
	private Temper temper;
	private Random dice = new Random();
	protected transient Logger logger;

	// Override initAg method to connect to the WebSocket server (body)
	public void initAg() {

		super.initAg();

		// Initialize the global variables
		myName = getTS().getAgArch().getAgName();
		Settings stts = getTS().getSettings();
		String temperStr 	= stts.getUserParameter( "temper" );
		String strategy 	= stts.getUserParameter( "strategy" );
		String address 		= stts.getUserParameter( "address" );
		int port 			= Integer.parseInt( stts.getUserParameter( "port" ) );
		logger = getTS().getLogger();

		// Initialize the agent temper and strategy
		temper = new Temper( temperStr, strategy );

		logger.info( "Body is at " + address + " : " + port );

		initBody( address, port );

	}

	private void initBody( String address, int port ) {
		// Connect to the Body
		try {
			URI bodyAddress = new URI( "ws://" + address + ":" + port );
			client = new WsClient( bodyAddress );
		} catch( Exception e ){
			stop( e.getMessage() );
		}

		// Connect the two handle functions to the client object
		client.setMsgHandler( new WsClientMsgHandler() {
			@Override
			public void handleMsg( String msg ) {
				vesnaHandleMsg( msg );
			}

			@Override
			public void handleError( Exception ex ) {
				vesnaHandleError( ex );
			}
		}  );

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

	// this method signals the mind about a perception
	private void sense( Literal perception ) {
		try {
			Message signal = new Message( "signal", myName, myName , perception );
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
	public void vesnaHandleMsg( String msg ) {
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
		System.out.println( "[" + myName + " ERROR] " + reason );
		kill_agent();
	}

	// Handles a connection error: prints a message and kills the agent
	public void vesnaHandleError( Exception ex ){
		System.out.println( "[" + myName + " ERROR] " + ex.getMessage() );
		kill_agent();
	}

	// Kills the agent calling the internal actions to drop all desires, intentions and events and then kill the agent;
	// This is necessary to avoid the agent to keep running after the kill_agent call ( that otherwise is simply enqueued ).
	private void kill_agent() {
		System.out.println( "[" + myName + " ERROR] Killing agent" );
		try {
			InternalAction drop_all_desires = getIA( ".drop_all_desires" );
			InternalAction drop_all_intentions = getIA( ".drop_all_intentions" );
			InternalAction drop_all_events = getIA( ".drop_all_events" );
			InternalAction action = getIA( ".kill_agent" );

			drop_all_desires.execute( getTS(), new Unifier(), new Term[] {} );
			drop_all_intentions.execute( getTS(), new Unifier(), new Term[] {} );
			drop_all_events.execute( getTS(), new Unifier(), new Term[] {} );
			action.execute( getTS(), new Unifier(), new Term[] { createString( myName ) } );
		} catch ( Exception e ) {
			e.printStackTrace();
		}
	}

	// Override the selectOption in order to consider Temper if needed
	public Option selectOption( List<Option> options ) {

		// If there is only one options or the options are without temper go with the default
		if ( options.size() == 1 || !areOptionsWithTemper( options ) )
			return super.selectOption( options );

		// Wrap the options inside an object Temper Selectable
		List<OptionWrapper> wrappedOptions = options.stream()
			.map( OptionWrapper::new )
			.collect( Collectors.toList() );

		// Select with temper
		try {
			return temper.select( wrappedOptions ).getOption();
		} catch ( NoValueException nve ) {
			stop( nve.getMessage() );
		}
		return null;
	}

	// Override the selectIntention in order to consider Temper if added
	public Intention selectIntention( Queue<Intention> intentions ) {

		logger.info( "I have " + intentions.size() + " intentions" );

		if ( intentions.size() == 1 || !areIntentionsWithPropensions(intentions ) )
			return super.selectIntention( intentions );
		List<IntentionWrapper> wrappedIntentions = new ArrayList<>( intentions ).stream()
			.map( IntentionWrapper::new )
			.collect( Collectors.toList() );
		try {
			Intention selected = temper.select( wrappedIntentions ).getIntention();
			Iterator<Intention> it = intentions.iterator();
			while( it.hasNext() ) {
				if ( it.next() == selected ) {
					it.remove();
					break;
				}
			}
			return selected;
		} catch ( NoValueException nve ) {
			stop( nve.getMessage() );
		}
		return null;
	}

	private boolean areOptionsWithTemper( List<Option> options ) {
		Literal propension = createLiteral( "temper", new VarTerm( "X" ) );
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

	private boolean areIntentionsWithPropensions( Queue<Intention> intentions ) {
		Literal propension = createLiteral( "propensions", new VarTerm( "X" ) );	
		for ( Intention intention : intentions ) {
			Plan p = intention.peek().getPlan();
			Pred l = p.getLabel();
			if ( l.hasAnnot() ) {
				for ( Term t : l.getAnnots() )
					if ( new Unifier().unifies( propension, t ) )
						return true;
			}
		}
		return false;
	}

}
