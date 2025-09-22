package vesna;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Random;

import static jason.asSyntax.ASSyntax.*;
import jason.asSyntax.*;
import jason.asSemantics.*;
import jason.asSyntax.parser.ParseException;
import jason.NoValueException;

public class Temper {

    private enum DecisionStrategy { MOST_SIMILAR, RANDOM };

    private Map<String, Integer> personality;
    private Map<String, Integer> mood;
    private DecisionStrategy strategy;
    private Random dice = new Random();

    public Temper( String temper, String strategy ) throws IllegalArgumentException {

        // The temper should always be set at this point
        if ( temper == null )
            throw new IllegalArgumentException( "Temper cannot be null" );

        // Initialize the new personality
        personality = new HashMap<>();

        try {
            // Load the personality into the Map
            Literal listLit = parseLiteral( temper );
            for ( Term term : listLit.getTerms() ) {
                Literal trait = ( Literal ) term;
                int value = ( int ) ( ( NumberTerm ) trait.getTerm( 0 ) ).solve();
                if ( value < 0 || value > 100 )
                    throw new IllegalArgumentException( "Trait value must be between 0 and 100, found:" + trait );
                personality.put( trait.getFunctor().toString(), value );
            }
        } catch ( ParseException pe ) {
            throw new IllegalArgumentException( pe.getMessage() + " Maybe one of the terms of personality is mispelled" );
        } catch ( NoValueException nve ) {
            throw new IllegalArgumentException( nve.getMessage() + " Maybe one of the terms is mispelled and does not contain a number" );
        }

        // Create the mood Map as a copy of the personality
        // The personality will stay fixed (or in the future change very slowly)
        // The mood instead can change in a very rapid way
        mood = new HashMap<>( personality );

        // Load the strategy
        if ( strategy == null )
            this.strategy = DecisionStrategy.MOST_SIMILAR;
        if ( strategy.equals( "most_similar" ) )
            this.strategy = DecisionStrategy.MOST_SIMILAR;
        else if ( strategy.equals( "random" ) )
            this.strategy = DecisionStrategy.RANDOM;
        else
            throw new IllegalArgumentException( "Decision Strategy Unknown: " + strategy );
    }

    public <T extends TemperSelectable> T select( List<T> choices ) throws NoValueException {
        List<Integer> weights = new ArrayList<>();

        for ( T choice : choices ) {

            int choiceWeight = 0;
            Pred label = choice.getLabel();

            Literal temperAnnot = label.getAnnot( "temper" );
            if ( temperAnnot == null )
                continue;

            ListTerm choiceTemper = ( ListTerm ) temperAnnot.getTerm( 0 );
            for ( Term traitTerm : choiceTemper ) {
                Atom trait = ( Atom ) traitTerm;
                if ( ! mood.keySet().contains( trait.getFunctor() ) )
                    continue;
                int traitMood = mood.get( trait.getFunctor() );
                try {
                    int traitValue = ( int ) ( (NumberTerm ) trait.getTerm( 0 ) ).solve();
                    if ( traitValue < 0 || traitValue > 100 )
                        throw new IllegalArgumentException("Trait value out of range, found: " + trait + ". The value should be inside [0, 100].");
                    if ( strategy == DecisionStrategy.RANDOM )
                        choiceWeight += traitMood * traitValue;
                    else if ( strategy == DecisionStrategy.MOST_SIMILAR )
                        choiceWeight += Math.abs( traitMood - traitValue );
                } catch ( NoValueException nve ) {
                    throw new NoValueException( "One of the plans has a mispelled annotation" );
                }
            }
            weights.add( choiceWeight );
        }

        T chosen = choices.get( 0 );
        if ( strategy == DecisionStrategy.RANDOM )
            chosen = choices.get( getWeightedRandomIdx( weights ) );
        else if ( strategy == DecisionStrategy.MOST_SIMILAR )
            chosen = choices.get( getMostSimilarIdx( weights ) );

        Literal effectList = chosen.getLabel().getAnnot( "effects" );
        if ( effectList != null )
            updateDynTemper( effectList );

        return chosen;
    }

    private int getWeightedRandomIdx( List<Integer> weights ) {
        int sum = weights.stream().reduce( 0, Integer::sum );
        int roll = dice.nextInt( sum );
        int currentMin = 0;
        for ( int i = 0; i < weights.size(); i++ ) {
            if ( roll > currentMin && roll < weights.get( i ) + currentMin )
                return i;
            currentMin += weights.get( i );
        }
        return 0;
    }

    private int getMostSimilarIdx( List<Integer> weights ) {
        int min = Integer.MAX_VALUE;
        int minIdx = -1;
        for ( int i = 0; i < weights.size(); i++ ) {
            if ( weights.get( i ) < min ) {
                min = weights.get( i );
                minIdx = i;
            }
        }
        return minIdx;
    }

    private void updateDynTemper( Literal effectList ) throws NoValueException {
        ListTerm effects = ( ListTerm ) effectList.getTerm( 0 );
        for ( Term effectTerm : effects ) {
            Literal effect = ( Literal ) effectTerm;
            if ( mood.get( effect.getFunctor().toString() ) != null ) {
                int moodValue = mood.get( effect.getFunctor().toString() );
                try {
                    int effectValue = ( int ) ( ( NumberTerm ) effect.getTerm( 0 ) ).solve();
                    if ( effectValue < - 100 || effectValue > 100 )
                    	throw new IllegalArgumentException("Effect value out of range: " + effectValue + ". It should be between [-100,100].");
                    if ( moodValue + effectValue > 100 )
                        mood.put( effect.getFunctor().toString(), 100 );
                    else if ( moodValue + effectValue < 0 )
                        mood.put( effect.getFunctor().toString(), 0 );
                    else
                        mood.put( effect.getFunctor().toString(), moodValue + effectValue );
                } catch ( NoValueException nve ) {
                    throw new NoValueException( "One of the plans has a mispelled annotation" );
                }
            }
        }
    }

}
