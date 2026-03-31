package vesna;

import jason.JasonException;
import jason.architecture.AgArch;
import jason.asSemantics.*;
import jason.asSyntax.*;
import jason.asSyntax.parser.ParseException;
import jason.runtime.RuntimeServicesFactory;
import jason.mas2j.ClassParameters;
import jason.bb.BeliefBase;
import jason.bb.DefaultBeliefBase;
import jason.infra.local.LocalAgArch;
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

/**
 * <p>
 * 	VesnaAgent class extends the Agent class making the agent embodied;
 * 	It connects to the body using a WebSocket connection;
 * </p>
 * <p>
 * 	It can use four parameters:
 * 	<ul>
 * 		<li> {@code address( ADDRESS )} and {@code port( PORT )} that describe the address and port of the WebSocket server;</li>
 * 		<li> {@code temper( [ LIST OF PROPENSIONS ] )} and {@code strategy( most_similar | random )} for the plan temper choice.</li>
 * 		<li> {@code strategy( most_similar | random )} for the plan temper choice.</li>
 * 	</ul>
 * <p>
 * In order to use it you should add to your .jcm:
 * <pre>
 * agent alice:alice.asl {
 * 	ag-class: 		vesna.VesnaAgent
 * 	address: 		localhost
 * 	port: 			8080
 * 	temper:			propensions([ ... ])
 * 	strategy: 		random
 * }
 * </pre>
 * @author Andrea Gatti
 */
public class VesnaAgent extends Agent{

	// GLOBAL VARIABLES
	/** WebSocket Client that connects with the body */
	private WsClient body;
	/** The temper of the agent */
	private Temper temper;
	/** The Reward Machine for CFR-based learning */
	private RewardMachine rewardMachine;
	/** The list of methods the dev wants to debug */
	private List<String> debugs;
	/** The logger necessary to print on the JaCaMo log */
	protected transient Logger logger;

	/** Initialize the agent with body and temper
	 * <p>
	 * Override initAg method in order to:
	 * <ul>
	 *	<li> connect to the body if needed; </li>
	 *	<li> initialize the temper if needed. </li>
	 * </ul>
	 */
	public void initAg() {

		super.initAg();

		Settings stts = getTS().getSettings();
		logger = getTS().getLogger();

		initDebug( stts );
		initTemper( stts );
		initRewardMachine( stts );
		initBody( stts );
	}

	private void initRewardMachine( Settings stts ) {
		String rmEnabled = stts.getUserParameter( "reward_machine" );
		if ( rmEnabled != null && rmEnabled.equals( "true" ) ) {
			rewardMachine = new RewardMachine();
			System.out.println( "[RM] Reward Machine initialized" );
		}
	}

	public RewardMachine getRewardMachine() {
		return rewardMachine;
	}

	private void initDebug( Settings stts ) {
		String debugStts = stts.getUserParameter( "vesnadebug" );
		debugs = new ArrayList<>();
		if ( debugStts == null )
			return;
		try{
			Literal debugList = parseLiteral( debugStts );
			debugs = debugList.getTerms().stream().map( Term::toString ).collect( Collectors.toList() );
		} catch( ParseException pe ) {
			logger.warning( "Invalid debug list: " + debugStts );
		}
	}

	private void initTemper( Settings stts ) {
		String temperStts = stts.getUserParameter( "temper" );
		String strategy = stts.getUserParameter( "strategy" );
		if ( temperStts == null )
			return;
		if ( strategy == null )
			strategy = "most_similar";

		// Try to load persisted personality first
		Map<String, Object> persisted = Temper.loadPersonalityFromFile();
		if ( persisted != null ) {
			// Merge persisted values with the configuration
			Map<String, Double> savedPersonality = (Map<String, Double>) persisted.get( "personality" );
			Map<String, Double> savedMood = (Map<String, Double>) persisted.get( "mood" );

			// Build new temper string with saved values
			// Use proper Jason NumberTerm format: 0.8 instead of 0.8000000000000002
			StringBuilder mergedTemper = new StringBuilder( "temper( " );
			boolean first = true;

			// Add personality traits
			for ( Map.Entry<String, Double> entry : savedPersonality.entrySet() ) {
				if ( !first ) mergedTemper.append( ", " );
				// Round to 3 decimal places for clean formatting
				double val = Math.round( entry.getValue() * 1000.0 ) / 1000.0;
				mergedTemper.append( entry.getKey() ).append( "(" ).append( val ).append( ")" );
				first = false;
			}
			// Add mood traits
			for ( Map.Entry<String, Double> entry : savedMood.entrySet() ) {
				if ( !first ) mergedTemper.append( ", " );
				double val = Math.round( entry.getValue() * 1000.0 ) / 1000.0;
				mergedTemper.append( entry.getKey() ).append( "(" ).append( val ).append( ")" )
					.append( "[mood]" );
				first = false;
			}

			mergedTemper.append( " )" );
			temperStts = mergedTemper.toString();
			System.out.println( "[PERSIST] Merged loaded personality: " + temperStts );
		}

		temper = new Temper( temperStts, strategy );
	}

	/**
	 * <p>
		* Initialize the Body connection through WebSocket.
		* @param	address	the address where the body is located
		* @param	port	the port where the body is listening
	 */
	private void initBody( Settings stts ) {
		String address = stts.getUserParameter( "address" );
		int port = Integer.parseInt( stts.getUserParameter( "port" ) );
		if ( address == null ) {
			logger.warning( "No body configured." );
			return;
		}
		try {
			URI bodyAddress = new URI( "ws://" + address + ":" + port );
			body = new WsClient( bodyAddress );
			body.setMsgHandler( new WsClientMsgHandler() {
				@Override public void handleMsg( String msg ) { bodyHandleMsg( msg ); }
				@Override public void handleError( Exception ex ) { bodyHandleError( ex );}
			}  );
			body.connect();
		} catch( Exception e ){
			stop( e.getMessage() );
		}

	}

	/** Performs a body action in the environment
	 * @param action The action to perform formatted into a JSON string
	*/
	public void perform( String action ) {
		body.send( action );
	}

	/** Signals the mind about a perception
	 * @param perception The perception to signal formatted as Jason Literal
	*/
	private void sense( Literal perception ) {
		try {
			Message signal = new Message( "signal", getTS().getAgArch().getAgName(), getTS().getAgArch().getAgName() , perception );
			getTS().getAgArch().sendMsg( signal );
		} catch ( Exception e ) {
			e.printStackTrace();
		}
	}

	/** Takes all the data from an event and senses a perception
	 * @param event The event to handle formatted as JSON object:
		* <pre>
		 * {
		 *   "type": "event_type",
		 *   "status": "event_status",
		 *   "reason": "event_reason"
		 * }
		* </pre>
	* It will <i>sense</i> a literal formatted as {@code event_type( event_status, event_reason )}.
	*/
	private void handleEvent( JSONObject event ) {
		String event_type = event.getString( "type" );
		String event_status = event.getString( "status" );
		String event_reason = event.getString( "reason" );
		Literal perception = createLiteral( event_type, createLiteral( event_status ), createLiteral( event_reason ) );
		sense(perception);
	}

	/**
	* Takes all the data from a sight and adds a belief
	* @param sight The sight to handle formatted as JSON object:
		* <pre>
		 * {
		 *   "sight": "object",
		 *   "id": 1234567890
		 * }
		* </pre>
		* It will <i>add a belief</i> formatted as {@code sight( object, id )}.
	*/
	private void handleSight( JSONObject sight ) {
		String object = sight.getString( "sight" );
		long id = sight.getLong( "id" );
		Literal sight_belief = createLiteral( "sight", createLiteral( object ), createNumber( id ) );
		try{
			addBel( sight_belief );
		} catch ( Exception e ) {
			e.printStackTrace();
		}
	}

	/** Handles incoming messages from the body.
	* Available types are: signal, sight.
	* @param msg The message received formatted as JSON string:
	* <pre>
	 * {
	 *   "sender": "body",
	 *   "receiver": "agent_name",
	 *   "type": "signal | sight",
	 *   "data": { ... }
	 * }
	 * </pre>
	*/
	public void bodyHandleMsg( String msg ) {
		System.out.println( "Received message: " + msg );
		JSONObject log = new JSONObject( msg );
		String sender = log.getString( "sender" );
		String receiver = log.getString( "receiver" );
		String type = log.getString( "type" );
		JSONObject data = log.getJSONObject( "data" );
		switch( type ){
			case "signal":
				handleEvent( data );
				break;
			case "sight":
				handleSight( data );
				break;
			default:
				logger.warning( "Unknown message type: " + type );
		}
	}

	/** Stops the agent: prints a message and kills the agent
	 * @param reason The reason why the agent is stopping
	 */
	private void stop( String reason ) {
		logger.severe( reason );
		kill_agent();
	}

	/** Handles a connection error: prints a message and kills the agent
	 * @param ex The exception raised
	 */
	public void bodyHandleError( Exception ex ){
		logger.severe( ex.getMessage() );
		kill_agent();
	}

	/** Kills the agent
	 * <p>
	 * It calls the internal actions to drop all desires, intentions and events and then kill the agent;
	 * This is necessary to avoid the agent to keep running after the kill_agent call ( that otherwise is simply enqueued ).
	 * </p>
	 */
	private void kill_agent() {
		logger.severe( "Killing agent" );
		if ( body != null )
			body.close();
		AgArch arch = ts.getAgArch();
		while ( arch != null ) {
			if ( arch instanceof LocalAgArch ) {
				( (LocalAgArch) arch ).stopAg();
				break;
			}
			arch = arch.getNextAgArch();
		}
	}

	/** Overrides the selectOption in order to consider Temper if needed
	 * <p>
	 * If there is only one option or the options are without temper it goes with the default selection;
	 * Otherwise it calls the temper select method.
	 * </p>
	 * @param options The list of options to choose from
	 * @return The selected option
	 * @see vesna.Temper#select(List) Temper.select(List)
	 */
	@Override
	public Option selectOption( List<Option> options ) {
		if ( options == null || options.isEmpty() )
			return null;
		if ( !hasTemper() || options.size() == 1 || !temper.hasOptionsAnnotation( options ) )
			return options.remove( 0 ); // this is what the super method does
		Option selected = temper.selectOption( options );
		System.out.println( temper.toString() );
		System.out.println( "[TEMPER] Selected plan: " + selected.getPlan().getLabel().getFunctor() );
		return selected;
	}

	/** Overrides the selectIntention in order to consider Temper if added
	 * <p>
	 * If there is only one intention or the intentions are without temper it goes with the default selection;
	 * Otherwise it calls the temper select method.
	 * </p>
	 * @param intentions The queue of intentions to choose from
	 * @return The selected intention
	 * @see vesna.Temper#select(List) Temper.select(List)
	 */
	public Intention selectIntention( Queue<Intention> intentions ) {
		if ( intentions.size() == 1 || !temper.hasIntentionsAnnotation( intentions ) )
			return intentions.poll(); // this is what the super method does
		return temper.selectIntention( intentions );
	}

	private boolean hasTemper() {
		return temper != null;
	}

	/** Get the Temper object (for CFR integration) */
	public Temper getTemper() {
		return temper;
	}

}
