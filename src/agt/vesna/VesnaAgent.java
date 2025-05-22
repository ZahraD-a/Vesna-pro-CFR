package vesna;

import jason.JasonException;
import jason.asSemantics.*;
import jason.asSyntax.*;
import jason.runtime.RuntimeServicesFactory;
import jason.stdlib.broadcast;

import static jason.asSyntax.ASSyntax.*;

import java.net.URI;
import java.text.ParseException;

import org.gradle.internal.impldep.org.apache.commons.lang.StringUtils;
import org.json.JSONObject;
import java.util.List;
import java.util.ArrayList;
import java.util.Queue;
import java.util.Iterator;
import java.util.Random;

// json imports
import org.json.JSONObject;
import org.json.JSONArray;

// VesnaAgent class extends the Agent class making the agent embodied;
// It connects to the body using a WebSocket connection;
// It needs two beliefs: address( ADDRESS ) and port( PORT ) that describe the address and port of the WebSocket server;
// In order to use it you should add to your .jcm:
// > agent alice:alice.asl {
// >      beliefs: address( localhost )
// >               port( 8080 )
// >      ag-class: vesna.VesnaAgent
// > }

public class VesnaAgent extends Agent{

    private WsClient client;
    private String my_name;

    public enum Propension {
        neutral,
        defensive,
        offensive
    }

    Propension propension = Propension.neutral;

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
        // Connect the body
        client.connect();

        // get the agent propension: if not setted in the jcm -> neutral
        Unifier propension_unifier = new Unifier();
        if ( believes( parseLiteral( "propension( Propension )" ), propension_unifier ) )
            propension = Propension.valueOf( propension_unifier.get( "Propension" ).toString() );
        System.out.println( "Got propension: " + propension );

        addBel( parseLiteral( "parsing_map( false )" ) );
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
        try {
            String event_type = event.getString( "type" );
            String event_status = event.getString( "status" );
            String event_reason = event.getString( "reason" );
            Literal perception = createLiteral( event_type, parseLiteral( event_status ), parseLiteral( event_reason ) );
            System.out.println( "Sensing " + perception.toString() );
            sense(perception);
        } catch ( Exception e ) {
            System.out.println( "Error parsing event: " + e.getMessage() );
        }
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

    private void handle_percept( JSONObject json ) {
        try {
            Literal percept = parseLiteral( json.getString( "percept" ) );
            sense( percept );
        } catch( Exception e ){
            e.printStackTrace();
        }
    }

    private void handle_coin( JSONObject json ) {
        try {
            System.out.println( json.toString() );
            String type = json.getString( "type" ); 
            switch( type ) {
                case "spawn":
                    Literal color = parseLiteral( json.getString( "midfield" ) );
                    Literal res = parseLiteral( json.getString( "name" ) );
                    addBel( createLiteral( "area", color, res ) );
                    break;
                case "gain":
                    Literal name = parseLiteral ( json.getString( "name" ) );
                    delBel( parseLiteral( "area( _, " + name + ")") );
                    sense( parseLiteral( "gained(" + name + ")" ) );
                    break;
                case "malus":
                    int amount = json.getInt( "amount" );
                    sense( parseLiteral( "malus(" + amount + ")" ) );
                    break;
            }
        } catch ( Exception e ) {
            System.out.println( "Error parsing coin: " + e.getMessage() );
        }
    }

    private void handle_env( JSONObject data ) {
        try {
            Literal color = parseLiteral( data.getString( "color" ) );
            sense( createLiteral( "new_pos", color ) );
        } catch ( Exception e ) {
            System.out.println( "Error parsing env: " + e.getMessage() );
        }
    }

    // this function handles incoming messages from the body
    // available types are: signal, sight
    public void vesna_handle_msg( String msg ) {
        System.out.println( "[[" + my_name + "]]" + msg );
        JSONObject log = new JSONObject( msg );
        // String sender = log.getString( "sender" );
        // String receiver = log.getString( "receiver" );
        String type = log.getString( "type" );
        JSONObject data = log.getJSONObject( "data" );
        switch( type ){
            case "signal":
                handle_event( data );
                break;
            case "percept":
                handle_percept( log );
                break;
            case "coin":
                handle_coin( data );
                break;
            case "env":
                handle_env( data );
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
        if ( options.size() == 1 || !isOptionWithPropension( options ) )
            return super.selectOption( options );
        try {
            return selectPropensionOption( options );
        } catch ( Exception e ){
            return null;
        }
    }

    private boolean isOptionWithPropension( List<Option> options ) {
        for ( Option option : options ) {
            try {
                Plan p = option.getPlan();
                Pred l = p.getLabel();
                Literal prop_lit = createLiteral( propension.name(), new VarTerm( "X" ) );
                if ( l.hasAnnot() ) {
                    Unifier u = new Unifier();
                    for ( Term annot : l.getAnnots() ) {
                        if ( u.unifies( prop_lit,annot )  )
                            return true;
                    }
                }
            } catch( Exception e ) { e.printStackTrace(); };
        }
        return false;
    }

    private Option selectPropensionOption( List<Option> options ) throws Exception {
        double total_weight = 0.0;
        List<Integer> weights = new ArrayList<>();
        for ( Option option : options ) {
            Plan p = option.getPlan();
            Pred l = p.getLabel();
            Literal propension_value = l.getAnnot( propension.name() );
            int weight = 50;
            if ( propension_value != null )
                weight =  (int) ( ( NumberTerm ) propension_value.getTerm( 0 ) ).solve();
            total_weight += weight;
            weights.add( weight );
        }
        int idx = get_weigthed_random_idx( weights );
        return options.get( idx );
    }

    private int get_weigthed_random_idx( List<Integer> weights ) {

        int total_sum = weights.stream().reduce( 0, Integer::sum );
        Random dice = new Random();
        int roll = dice.nextInt( total_sum );
        int current_min = 0;
        for ( int i = 0; i < weights.size(); i++ ) {
            if ( roll > current_min && roll < weights.get( i ) + current_min )
                return i;
            current_min += weights.get( i );
        }
        return 0;
    }

}
