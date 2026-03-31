package vesna;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.Queue;
import java.util.ArrayList;
import java.util.Random;
import java.util.Iterator;
import java.util.Set;
import java.util.HashSet;
import java.util.stream.Collectors;
import java.io.*;
import java.nio.file.*;

import static jason.asSyntax.ASSyntax.*;
import jason.asSyntax.*;
import jason.asSemantics.*;
import jason.asSyntax.parser.ParseException;
import jason.NoValueException;

/** This class implements the temper of the agent
 * <p>
 * The temper of an agent is subdivided into:
 * <ul>
 * <li> <b>personality:</b> for the moment it does never change. <i>In the future</i>, it could change based on mood but very slowly;
 * <li> <b>mood:</b> it changes applying plan post-actions if provided.
 * </ul>
 * The agent can apply two decision strategies:
 * <ul>
 * <li> <b>Most similar:</b> deterministic, it chooses always the plan with personality and mood more similar to the current ones;
 * <li> <b>Random:</b> undeterministic, it chooses with a weighted random based on the similarity between the plan annotations and the current temper.
 * </ul>
 */
public class Temper {

    /** Decision Strategy is an enumerable between most similar and random */
    private enum DecisionStrategy { MOST_SIMILAR, RANDOM }

    /** Personality is the persistent part of the agent temper */
    private Map<String, Double> personality;
    /** Mood is the mutable part of the agent temper */
    private Map<String, Double> mood;
    /** The agent decision strategy */
    private DecisionStrategy strategy;
    /** A dice necessary to generate random numbers */
    private Random dice = new Random();

    // ==================== CFR EXECUTION TRACE ====================
    /** Minimal trace for CFR: each decision + outcome */
    public static class TraceEntry {
        public final long timestamp;
        public final String trigger;           // What goal triggered this
        public final List<String> options;      // Available plans
        public final int selectedIndex;         // Which was chosen
        public final Map<String, Double> personalityAtDecision;
        public final Map<String, Double> moodAtDecision;
        public final List<Double> weights;      // Weights for each option (for CFR)
        public final List<Map<String, Double>> planAnnotations;  // Each plan's trait values
        public double reward = 0.0;             // Set later when outcome known

        TraceEntry(String trig, List<String> opts, int sel, Map<String, Double> pers, Map<String, Double> mod, List<Double> wts, List<Map<String, Double>> annotations) {
            timestamp = System.currentTimeMillis();
            trigger = trig;
            options = new ArrayList<>(opts);
            selectedIndex = sel;
            personalityAtDecision = new HashMap<>(pers);
            moodAtDecision = new HashMap<>(mod);
            weights = new ArrayList<>(wts);
            planAnnotations = new ArrayList<>();
            for (Map<String, Double> ann : annotations) {
                planAnnotations.add(new HashMap<>(ann));
            }
        }

        @Override
        public String toString() {
            return "Trace[" + trigger + ": selected=" + options.get(selectedIndex) + " reward=" + reward + "]";
        }
    }

    private List<TraceEntry> trace = new ArrayList<>();
    private TraceEntry pendingEntry = null;  // Current decision waiting for reward
    private Map<String, Double> cumulativeRegret = new HashMap<>();  // Per-trait cumulative regret
    private double cfrLearningRate = 0.1;   // CFR learning rate - higher for faster personality discovery
    private static final String PERSONALITY_FILE = "personality.json";  // Persistence file

    // ==================== CFR: EXTENSIVE-FORM GAME STRUCTURE ====================
    /**
     * CFR Data for an Information Set (decision point).
     * In extensive-form games, each decision point is an information set.
     */
    public static class InformationSet {
        public final String name;              // e.g., "stage1", "stage2", "stage3"
        public final Map<String, Double> cumulativeRegret;  // Cumulative regret per action
        public final Map<String, Double> strategySum;       // Sum of strategies for averaging
        public int visitCount;                 // How many times this infoset was reached

        public InformationSet(String name) {
            this.name = name;
            this.cumulativeRegret = new HashMap<>();
            this.strategySum = new HashMap<>();
            this.visitCount = 0;
        }
    }

    /** Map of information sets in the game tree */
    private Map<String, InformationSet> informationSets = new HashMap<>();

    /** Current episode's decisions for CFR learning */
    private List<TraceEntry> currentEpisodeDecisions = new ArrayList<>();

    /** Rewards received at each stage of current episode */
    private Map<String, Double> stageRewards = new HashMap<>();

    /** Total episode reward */
    private double totalEpisodeReward = 0.0;

    /** Discount factor for future rewards */
    private static final double GAMMA = 0.9;

    /**
     * Get or create an information set for a stage.
     */
    private InformationSet getInformationSet(String stageName) {
        return informationSets.computeIfAbsent(stageName, InformationSet::new);
    }

    /**
     * Normalize plan labels: strip quotes and map Jason duplicates to original.
     */
    private String normalizePlanLabel(String label) {
        if (label == null) return null;
        String cleaned = label.replaceAll("^\"|\"$", "");
        if (cleaned.matches("p__\\d+")) return "p2";
        return cleaned;
    }

    /**
     * Get the expected (average) reward for a plan based on historical data.
     */
    private double getExpectedReward(String planLabel) {
        // For extensive-form games, we need to compute the expected value
        // through the game tree from this information set.
        // This is a simplified version - proper CFR would compute counterfactual values.
        InformationSet infoset = informationSets.get(planLabel);
        if (infoset == null || infoset.strategySum.isEmpty()) {
            return 0.0;
        }
        // Return the average strategy value as proxy
        double sum = 0.0;
        for (Double val : infoset.strategySum.values()) {
            sum += val;
        }
        return sum / Math.max(1, infoset.strategySum.size());
    }

    /**
     * Print CFR statistics for all information sets.
     */
    public void printCFRStats() {
        System.out.println("\n==================== CFR STATISTICS ====================");

        // Detect scenario type
        boolean isCoffeeScenario = false;
        for (String name : informationSets.keySet()) {
            InformationSet infoset = informationSets.get(name);
            for (String action : infoset.cumulativeRegret.keySet()) {
                if (action.contains("coffee") || action.contains("shop") || action.contains("home")) {
                    isCoffeeScenario = true;
                    break;
                }
            }
        }

        if (isCoffeeScenario) {
            // Print Coffee Decision cumulative regrets
            System.out.println("\n  [Coffee Decision] Cumulative Regrets:");
            InformationSet rootSet = informationSets.get("root");
            if (rootSet != null) {
                System.out.println("    try_new_shop:    " + String.format("%.3f", rootSet.cumulativeRegret.getOrDefault("try_new_shop", 0.0)));
                System.out.println("    go_regular_shop: " + String.format("%.3f", rootSet.cumulativeRegret.getOrDefault("go_regular_shop", 0.0)));
                System.out.println("    make_at_home:    " + String.format("%.3f", rootSet.cumulativeRegret.getOrDefault("make_at_home", 0.0)));

                // Compute implied strategy from regrets
                double totalPos = 0.0;
                for (Double r : rootSet.cumulativeRegret.values()) {
                    if (r > 0) totalPos += r;
                }
                if (totalPos > 0) {
                    System.out.println("\n  Implied Strategy (from regrets):");
                    System.out.println("    try_new_shop:    " + String.format("%.1f%%",
                        Math.max(0, rootSet.cumulativeRegret.getOrDefault("try_new_shop", 0.0)) / totalPos * 100));
                    System.out.println("    go_regular_shop: " + String.format("%.1f%%",
                        Math.max(0, rootSet.cumulativeRegret.getOrDefault("go_regular_shop", 0.0)) / totalPos * 100));
                    System.out.println("    make_at_home:    " + String.format("%.1f%%",
                        Math.max(0, rootSet.cumulativeRegret.getOrDefault("make_at_home", 0.0)) / totalPos * 100));
                }
            }
        } else {
            // Print Bridge Crossing cumulative regrets
            if (!rpsCumulativeRegret.isEmpty()) {
                System.out.println("\n  [Bridge Crossing] Cumulative Regrets:");
                System.out.println("    Carefully:     " + String.format("%.3f", rpsCumulativeRegret.getOrDefault("carefully", 0.0)));
                System.out.println("    Boldly:        " + String.format("%.3f", rpsCumulativeRegret.getOrDefault("boldly", 0.0)));
                System.out.println("    Test Steps:    " + String.format("%.3f", rpsCumulativeRegret.getOrDefault("test_steps", 0.0)));
                System.out.println("    Alternative:   " + String.format("%.3f", rpsCumulativeRegret.getOrDefault("alternative", 0.0)));
                System.out.println("    Wait:          " + String.format("%.3f", rpsCumulativeRegret.getOrDefault("wait", 0.0)));
            }
        }

        // Print extensive-form game information sets
        System.out.println("\n  Information Sets: " + informationSets.size());
        for (Map.Entry<String, InformationSet> entry : informationSets.entrySet()) {
            InformationSet infoset = entry.getValue();
            System.out.println("\n  [" + infoset.name + "] visited " + infoset.visitCount + " times");
            if (!infoset.cumulativeRegret.isEmpty()) {
                System.out.println("    Cumulative Regrets:");
                for (Map.Entry<String, Double> regret : infoset.cumulativeRegret.entrySet()) {
                    System.out.println("      " + regret.getKey() + ": " + String.format("%.3f", regret.getValue()));
                }
            }
            if (!infoset.strategySum.isEmpty()) {
                System.out.println("    Average Strategy:");
                for (Map.Entry<String, Double> strat : infoset.strategySum.entrySet()) {
                    double avgStrat = strat.getValue() / Math.max(1, infoset.visitCount);
                    System.out.println("      " + strat.getKey() + ": " + String.format("%.3f", avgStrat));
                }
            }
        }
        System.out.println("========================================================\n");
    }

    public Temper( String temper, String strategy ) throws IllegalArgumentException {

        // The temper should always be set at this point
        if ( temper == null )
            throw new IllegalArgumentException( "Temper cannot be null" );

        // Initialize the new personality
        personality = new HashMap<>();
        mood = new HashMap<>();
        cumulativeRegret = new HashMap<>();

        try {
            // Load the personality into the Map
            Literal listLit = parseLiteral( temper );
            for ( Term term : listLit.getTerms() ) {
                Literal trait = ( Literal ) term;
                double value = ( double ) ( ( NumberTerm ) trait.getTerm( 0 ) ).solve();
                if ( trait.hasAnnot( createLiteral( "mood" ) ) ) {
                    if ( value < -1.0 || value > 1.0 )
                        throw new IllegalArgumentException( "Trait value for mood must be between -1 and 1, found:" + trait );
                    mood.put( trait.getFunctor().toString(), value );
                    continue;
                } else {
                    if ( value < 0.0 || value > 1.0 )
                        throw new IllegalArgumentException( "Trait value for personality must be between 0 and 1, found:" + trait );
                    personality.put( trait.getFunctor().toString(), value );
                }
            }
        } catch ( ParseException pe ) {
            throw new IllegalArgumentException( pe.getMessage() + " Maybe one of the terms of personality is mispelled" );
        } catch ( NoValueException nve ) {
            throw new IllegalArgumentException( nve.getMessage() + " Maybe one of the terms is misspelled and does not contain a number" );
        }

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

    public double computeWeight( Pred label ) throws NoValueException {
        double choiceWeight = 0;

        Literal temperAnnot = label.getAnnot( "temper" );
        if ( temperAnnot == null )
            return choiceWeight;

        ListTerm choiceTemper = ( ListTerm ) temperAnnot.getTerm( 0 );
        for ( Term traitTerm : choiceTemper ) {
            Atom trait = ( Atom ) traitTerm;
            if ( ! mood.keySet().contains( trait.getFunctor().toString() ) && ! personality.keySet().contains( trait.getFunctor().toString() ) )
                continue;
            double traitTemper;
            if ( mood.keySet().contains( trait.getFunctor().toString() ) )
                traitTemper = mood.get( trait.getFunctor().toString() );
            else
                traitTemper = personality.get( trait.getFunctor().toString() );
            try {
                double traitValue = ( double ) ( (NumberTerm ) trait.getTerm( 0 ) ).solve();
                if ( traitValue < -1.0 || traitValue > 1.0 )
                    throw new IllegalArgumentException("Trait value out of range, found: " + trait + ". The value should be inside [0, 1].");
                if ( strategy == DecisionStrategy.RANDOM )
                    choiceWeight += traitTemper * traitValue;
                else if ( strategy == DecisionStrategy.MOST_SIMILAR )
                    choiceWeight += Math.abs( traitTemper - traitValue );
            } catch ( NoValueException nve ) {
                throw new NoValueException( "One of the plans has a misspelled annotation" );
            }
        }
        return choiceWeight;
    }

    public boolean hasOptionsAnnotation( List<Option> options ) {
    	List<OptionWrapper> wrappedOptions = options.stream()
    		.map( OptionWrapper::new )
    		.collect( Collectors.toList() );
    	return hasAnnotation( wrappedOptions );
    }

    public boolean hasIntentionsAnnotation( Queue<Intention> intentions ) {
    	List<IntentionWrapper> wrappedIntentions = intentions.stream()
    		.map( IntentionWrapper::new )
    		.collect( Collectors.toList() );
    	return hasAnnotation( wrappedIntentions );
    }

    private <T extends TemperSelectable> boolean hasAnnotation( List<T> choices ) {
        Literal annotPattern = createLiteral( "temper", new VarTerm( "X" ) );
        for ( T choice : choices ) {
            Pred l = choice.getLabel();
            if ( l.hasAnnot() ) {
                for ( Term t : l.getAnnots() ) {
                    if ( new Unifier().unifies( annotPattern, t ) )
                        return true;
                }
            }
        }
        return false;
    }

    public Option selectOption( List<Option> options ) {
    	List<OptionWrapper> wrappedOptions = options.stream()
			.map( OptionWrapper::new )
			.collect( Collectors.toList() );
		try {
			return select( wrappedOptions ).getOption();
		} catch ( NoValueException e ) {
			return null;
		}
    }

    public Intention selectIntention( Queue<Intention> intentions ) {
    	List<IntentionWrapper> wrappedIntentions = new ArrayList<>( intentions ).stream()
     		.map( IntentionWrapper::new )
     		.collect( Collectors.toList() );
       try {
        	Intention selected = select( wrappedIntentions ).getIntention();
         	Iterator<Intention> it = intentions.iterator();
          	while( it.hasNext() ) {
	           	if ( it.next() == selected ) {
	           		it.remove();
	             	break;
	           }
           }
           Literal effectList = selected.peek().getPlan().getLabel().getAnnot( "effects" );
           if ( effectList != null )
               updateDynTemper( effectList );
           return selected;
       } catch ( NoValueException e ) {
	       return null;
       }
    }

    public <T extends TemperSelectable> T select( List<T> choices ) throws NoValueException {
        List<Double> weights = new ArrayList<>();

        for ( T choice : choices ) {
            weights.add( computeWeight( choice.getLabel() ) );
        }

        T chosen = null;
        int chosenIdx = -1;
        if ( strategy == DecisionStrategy.RANDOM ) {
        	chosenIdx = getWeightedRandomIdx( weights );
            chosen = choices.get( chosenIdx );
        } else if ( strategy == DecisionStrategy.MOST_SIMILAR ) {
            chosenIdx = getMostSimilarIdx( weights );
            chosen = choices.get( chosenIdx );
        }
        if ( chosen == null ) {
        	chosenIdx = 0;
            chosen = choices.get( chosenIdx );
        }

        // Record decision in trace for CFR (pass weights for proper counterfactual)
        recordDecision( choices, chosenIdx, weights );

        return chosen;
    }

    // ==================== CFR TRACE METHODS ====================

    /** Current decision stage (for tracking information sets) */
    private String currentStage = "root";

    /** Set the current decision stage */
    public void setCurrentStage(String stage) {
        this.currentStage = stage;
    }

    /** Record a decision in the current episode for CFR learning */
    private <T extends TemperSelectable> void recordDecision( List<T> choices, int selectedIdx, List<Double> weights ) {
        List<String> optionLabels = choices.stream()
            .map( c -> normalizePlanLabel(c.getLabel().getFunctor()) )
            .collect( Collectors.toList() );

        // Extract plan annotations for CFR
        List<Map<String, Double>> annotations = new ArrayList<>();
        for (T choice : choices) {
            Map<String, Double> planTraits = new HashMap<>();
            Literal annot = choice.getLabel().getAnnot("temper");
            if (annot != null) {
                ListTerm traits = (ListTerm) annot.getTerm(0);
                for (Term traitTerm : traits) {
                    Literal trait = (Literal) traitTerm;
                    try {
                        double value = ((NumberTerm) trait.getTerm(0)).solve();
                        planTraits.put(trait.getFunctor(), value);
                    } catch (NoValueException e) {
                        // Skip invalid traits
                    }
                }
            }
            annotations.add(planTraits);
        }

        // Create trace entry for current episode
        TraceEntry entry = new TraceEntry(currentStage, optionLabels, selectedIdx,
            new HashMap<>(personality), new HashMap<>(mood), weights, annotations);
        currentEpisodeDecisions.add(entry);

        // Update information set visit count
        InformationSet infoset = getInformationSet(currentStage);
        infoset.visitCount++;

        // Record the action taken in strategy sum
        String chosenAction = optionLabels.get(selectedIdx);
        infoset.strategySum.put(chosenAction,
            infoset.strategySum.getOrDefault(chosenAction, 0.0) + 1.0);

        // Compute probabilities for logging
        double[] probs = computeActionProbabilities(weights);

        StringBuilder sb = new StringBuilder();
        sb.append("[CFR] Stage=").append(currentStage)
          .append(" Decision #").append(currentEpisodeDecisions.size()).append(":\n");
        for (int i = 0; i < optionLabels.size(); i++) {
            sb.append("    ").append(optionLabels.get(i))
              .append(": weight=").append(String.format("%.3f", weights.get(i)))
              .append(", prob=").append(String.format("%.1f%%", probs[i] * 100));
            if (i == selectedIdx) sb.append(" <-- SELECTED");
            sb.append("\n");
        }
        System.out.print(sb.toString());
    }

    /**
     * Called when a stage outcome is received.
     * Records the reward for this stage.
     */
    public void recordStageOutcome(String stage, double reward) {
        stageRewards.put(stage, reward);
        totalEpisodeReward += reward;

        // Update pending entry with reward
        if (!currentEpisodeDecisions.isEmpty()) {
            for (TraceEntry entry : currentEpisodeDecisions) {
                if (entry.trigger.equals(stage) && entry.reward == 0.0) {
                    entry.reward = reward;
                    break;
                }
            }
        }
        System.out.println("[CFR] Stage " + stage + " reward: " + reward);
    }

    /** Get full trace for CFR analysis */
    public List<TraceEntry> getTrace() { return new ArrayList<>(currentEpisodeDecisions); }

    /** Get personality snapshot */
    public Map<String, Double> getPersonality() { return new HashMap<>(personality); }

    // ==================== CFR LEARNING ====================

    /**
     * PROPER CFR for Extensive-Form Games.
     *
     * Computes counterfactual regret at each information set and updates
     * personality via regret matching.
     *
     * CFR Algorithm:
     * 1. For each information set I visited in episode:
     *    a. Get the counterfactual value v(I, σ) - actual value received
     *    b. For each action a at I:
     *       - Compute counterfactual value if we had taken a: v(I, σ_{I→a})
     *       - Instant regret: r(I, a) = v(I, σ_{I→a}) - v(I, σ)
     *       - Update cumulative regret: R(I, a) += r(I, a)
     * 2. Update strategy via regret matching:
     *    σ^{T+1}(I, a) = [R^T(I, a)]+ / Σ[R^T(I, a')]^+
     * 3. Update personality to match the strategy that minimizes regret
     */
    public void updatePersonalityFromCFR() {
        if (currentEpisodeDecisions.isEmpty()) {
            return;
        }

        // Detect scenario type directly from information sets
        boolean isCoffeeScenario = detectCoffeeScenario();
        boolean isRPSScenario = detectRPSScenario();

        if (isCoffeeScenario) {
            updatePersonalityFromCoffeeRegret();
        } else if (isRPSScenario) {
            updatePersonalityFromRPSRegret();
        } else {
            updatePersonalityFromBridgeRegret();
        }
    }

    /**
     * Detect if we're running the coffee decision scenario.
     */
    private boolean detectCoffeeScenario() {
        for (InformationSet infoset : informationSets.values()) {
            for (String action : infoset.cumulativeRegret.keySet()) {
                if (action.contains("coffee") || action.contains("shop") || action.contains("home")) {
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * Detect if we're running the RPS scenario.
     */
    private boolean detectRPSScenario() {
        return !rpsCumulativeRegret.isEmpty();
    }

    /**
     * Get expected reward for a bridge action (like RPS payoff matrix).
     * This represents the average outcome if this action is taken.
     */
    private double getBridgeExpectedReward(String action) {
        int idx = bridgeActionToIndex(action);
        if (idx >= 0 && idx < BRIDGE_EXPECTED_REWARDS.length) {
            return BRIDGE_EXPECTED_REWARDS[idx];
        }
        return 0.0;  // Default for unknown actions
    }

    /**
     * Compute the future value from this decision point through the rest of the episode.
     * This accounts for the extensive-form structure - decisions affect future options.
     */
    private double computeFutureValue(TraceEntry entry, List<TraceEntry> allDecisions) {
        double value = entry.reward;

        // Find subsequent decisions and add their discounted rewards
        int entryIndex = allDecisions.indexOf(entry);
        for (int i = entryIndex + 1; i < allDecisions.size(); i++) {
            TraceEntry subsequent = allDecisions.get(i);
            value += subsequent.reward * Math.pow(GAMMA, i - entryIndex);
        }

        return value;
    }

    /**
     * Estimate the counterfactual value if we had taken an alternative action.
     * For bridge crossing, use the expected reward for each action type.
     */
    private double estimateCounterfactualValue(Map<String, Double> altTraits,
                                               Map<String, Double> personalityAtDecision,
                                               double actualValue) {
        // Determine which bridge strategy this action profile corresponds to
        // and return its expected reward (counterfactual value)
        double cautious = altTraits.getOrDefault("cautious", 0.5);
        double bold = altTraits.getOrDefault("bold", 0.5);

        // Map personality profile to expected reward based on bridge success rates
        // carefully: -0.2, boldly: 0.8, test_steps: 0.2, alternative: 0.4, wait: 0.0
        if (cautious > 0.7 && bold < 0.3) {
            return -0.2;  // carefully - mostly fails
        } else if (cautious < 0.3 && bold > 0.7) {
            return 0.8;   // boldly - mostly succeeds (90% success rate)
        } else if (cautious > 0.6 && bold < 0.5) {
            return 0.2;   // test_steps - moderate
        } else if (cautious > 0.4 && cautious < 0.6 && bold > 0.4 && bold < 0.6) {
            return 0.4;   // alternative - good success rate
        } else {
            return 0.0;   // wait - 50/50
        }
    }

    /**
     * Compute alignment between plan traits and personality.
     * Returns 1.0 for perfect match, 0.0 for no match, -1.0 for opposite.
     */
    private double computePersonalityAlignment(Map<String, Double> planTraits,
                                                Map<String, Double> personality) {
        double dotProduct = 0.0;
        double normPlan = 0.0;
        double normPers = 0.0;

        Set<String> allTraits = new HashSet<>();
        allTraits.addAll(planTraits.keySet());
        allTraits.addAll(personality.keySet());

        for (String trait : allTraits) {
            double planVal = planTraits.getOrDefault(trait, 0.0);
            double persVal = personality.getOrDefault(trait, 0.5); // Default to neutral

            dotProduct += planVal * persVal;
            normPlan += planVal * planVal;
            normPers += persVal * persVal;
        }

        if (normPlan == 0.0 || normPers == 0.0) return 0.0;
        return dotProduct / (Math.sqrt(normPlan) * Math.sqrt(normPers));
    }

    /**
     * Update personality based on regret matching across all information sets.
     *
     * The key insight: personality should evolve to favor the actions
     * that have positive cumulative regret (i.e., we regret not taking them).
     */
    private void updatePersonalityViaRegretMatching() {
        Map<String, Double> personalityGradients = new HashMap<>();
        for (String trait : personality.keySet()) {
            personalityGradients.put(trait, 0.0);
        }

        // Aggregate gradients from all information sets
        for (InformationSet infoset : informationSets.values()) {
            if (infoset.cumulativeRegret.isEmpty()) continue;

            // Find actions with positive regret (things we should have done)
            List<Map.Entry<String, Double>> positiveRegrets = new ArrayList<>();
            double totalPositiveRegret = 0.0;

            for (Map.Entry<String, Double> entry : infoset.cumulativeRegret.entrySet()) {
                if (entry.getValue() > 0) {
                    positiveRegrets.add(entry);
                    totalPositiveRegret += entry.getValue();
                }
            }

            if (totalPositiveRegret == 0) continue;

            // For each positive regret action, compute desired personality change
            // (simplified - assumes we know which traits favor which actions)
            for (Map.Entry<String, Double> regretEntry : positiveRegrets) {
                double regretWeight = regretEntry.getValue() / totalPositiveRegret;

                // Update personality towards traits that favor this action
                // This is a heuristic - proper implementation would use plan annotations
                for (String trait : personality.keySet()) {
                    double gradient = regretWeight * 0.1; // Learning rate
                    personalityGradients.put(trait,
                        personalityGradients.get(trait) + gradient);
                }
            }
        }

        // Apply gradients to personality
        for (String trait : personality.keySet()) {
            double gradient = personalityGradients.get(trait);
            if (Math.abs(gradient) < 0.001) continue;

            double oldValue = personality.get(trait);
            double newValue = oldValue + cfrLearningRate * gradient;
            newValue = Math.max(0.0, Math.min(1.0, newValue));

            personality.put(trait, newValue);

            if (Math.abs(newValue - oldValue) > 0.001) {
                System.out.println("[CFR] Personality update: " + trait + " " +
                    String.format("%.3f", oldValue) + " -> " + String.format("%.3f", newValue));
            }
        }
    }

    /**
     * Compute action probabilities from weights using softmax normalization.
     */
    private double[] computeActionProbabilities(List<Double> weights) {
        double[] probs = new double[weights.size()];

        double minWeight = Double.MAX_VALUE;
        for (double w : weights) {
            minWeight = Math.min(minWeight, w);
        }

        double sum = 0.0;
        for (int i = 0; i < weights.size(); i++) {
            probs[i] = Math.exp(weights.get(i) - minWeight);
            sum += probs[i];
        }

        if (sum > 0) {
            for (int i = 0; i < probs.length; i++) {
                probs[i] /= sum;
            }
        } else {
            for (int i = 0; i < probs.length; i++) {
                probs[i] = 1.0 / probs.length;
            }
        }

        return probs;
    }

    /** Start new episode (clear trace, but keep regrets for CFR convergence) */
    public void startNewEpisode() {
        System.out.println("[CFR] Episode complete. Decisions: " + currentEpisodeDecisions.size() +
            ", Total reward: " + String.format("%.2f", totalEpisodeReward));
        printHistoricalStats();

        // Print personality before CFR update
        System.out.println("[CFR] Personality BEFORE CFR update: " + formatPersonalitySimple());

        updatePersonalityFromCFR();

        // Print personality after CFR update
        System.out.println("[CFR] Personality AFTER CFR update:  " + formatPersonalitySimple());

        savePersonality();
        currentEpisodeDecisions.clear();
        stageRewards.clear();
        totalEpisodeReward = 0.0;
        currentStage = "root";

        // CFR: Keep cumulative regrets across episodes (never reset!)
        // The average strategy (strategySum / visitCount) converges to equilibrium
        System.out.println("[CFR] Regrets preserved for convergence (not reset)");
    }

    /**
     * Format personality as simple string (e.g., "cautious=0.750 bold=0.250").
     */
    private String formatPersonalitySimple() {
        StringBuilder sb = new StringBuilder();
        sb.append("{");
        boolean first = true;
        for (Map.Entry<String, Double> entry : personality.entrySet()) {
            if (!first) sb.append(" ");
            sb.append(entry.getKey()).append("=").append(String.format("%.3f", entry.getValue()));
            first = false;
        }
        sb.append("}");
        return sb.toString();
    }

    /** Print historical performance statistics */
    private void printHistoricalStats() {
        if (planStats.isEmpty()) return;
        System.out.println("\n--- Historical Performance ---");
        for (String plan : new String[]{"try_new_shop", "go_regular_shop", "make_at_home"}) {
            PlanStats stats = planStats.get(plan);
            if (stats != null && stats.attempts > 0) {
                System.out.println(String.format("  %s: %d attempts, %.1f%% success, avg reward=%.2f",
                    plan, stats.attempts, stats.getSuccessRate() * 100, stats.getAverageReward()));
            }
        }
        System.out.println("-------------------------------\n");
    }

    // ==================== RPS-CFR: ROCK-PAPER-SCISSORS CFR ====================

    /** RPS Payoff matrix: payoff[agent][opp] */
    private static final double[][] RPS_PAYOFF = {
        // opp: Rock,  Paper, Scissors
        {   0.0,   -1.0,    1.0    },  // agent: Rock
        {   1.0,    0.0,   -1.0    },  // agent: Paper
        {  -1.0,    1.0,    0.0    }   // agent: Scissors
    };

    private static final String[] RPS_ACTIONS = {"rock", "paper", "scissors"};

    /** Cumulative regret for each RPS action */
    private Map<String, Double> rpsCumulativeRegret = new HashMap<>();

    /** Track current RPS decision for CFR */
    private String currentAgentMove = null;
    private String currentOppMove = null;

    /**
     * Record RPS game outcome and compute CFR regrets.
     * This is the main CFR entry point for RPS.
     */
    public void recordRPSOutcome(String agentMove, String oppMove, double reward) {
        currentAgentMove = agentMove;
        currentOppMove = oppMove;

        int agentIdx = actionToIndex(agentMove);
        int oppIdx = actionToIndex(oppMove);

        if (agentIdx < 0 || oppIdx < 0) {
            System.out.println("[RPS-CFR] Invalid move: agent=" + agentMove + ", opp=" + oppMove);
            return;
        }

        // Compute counterfactual regrets for unchosen actions
        System.out.println("[RPS-CFR] Computing regrets (actual reward: " + reward + "):");

        for (int a = 0; a < 3; a++) {
            if (a == agentIdx) continue; // Skip chosen action

            String actionName = RPS_ACTIONS[a];

            // Counterfactual: "What if I had played 'a' instead?"
            double counterfactualReward = RPS_PAYOFF[a][oppIdx];

            // Instant regret = counterfactual - actual
            double regret = counterfactualReward - reward;

            // Update cumulative regret
            double currentRegret = rpsCumulativeRegret.getOrDefault(actionName, 0.0);
            rpsCumulativeRegret.put(actionName, currentRegret + regret);

            System.out.println(String.format("  Regret(%s) = %.1f - %.1f = %.2f (cumulative: %.2f)",
                actionName, counterfactualReward, reward, regret, currentRegret + regret));
        }

        // NOTE: Personality updates moved to episode-end (cfr_episode) only
        // This prevents rapid saturation and allows for stable learning

        // Add to total episode reward
        totalEpisodeReward += reward;
    }

    /**
     * Expected success rates for bridge crossing strategies.
     * These represent the counterfactual "what would have happened on average?"
     *
     * IMPORTANT: These are AVERAGE outcomes, not best-case.
     * In a learning environment, the agent needs to experience BOTH success and failure
     * to learn which personality works better.
     */
    private static final double[] BRIDGE_EXPECTED_REWARDS = {
        0.0,   // carefully: 50% success, 50% failure → 0.5*1 + 0.5*(-1) = 0.0 (BALANCED)
        0.0,   // boldly: 50% success, 50% failure → 0.5*1 + 0.5*(-1) = 0.0 (BALANCED)
        0.0,   // test_steps: 50% success, 50% failure → 0.0 (BALANCED)
        0.0,   // alternative: 50% success, 50% failure → 0.0 (BALANCED)
        0.0    // wait: 50% success, 50% failure → 0.0 (BALANCED)
    };

    private static final String[] BRIDGE_ACTIONS = {
        "carefully", "boldly", "test_steps", "alternative", "wait"
    };

    /**
     * Record bridge/coffee decision outcome.
     * Like RPS, we compute counterfactual regrets for ALL alternatives at episode end.
     *
     * CFR ALGORITHM (from article):
     * 1. Actual reward received: reward
     * 2. For each alternative plan a:
     *    regret(a) = expected_reward(a) - actual_reward
     * 3. Cumulative regret: R(a) += regret(a)
     * 4. Strategy update at episode end via regret matching
     */
    public void recordBridgeOutcome(String strategy, double reward) {
        currentAgentMove = strategy;
        currentOppMove = null; // No opponent in single-agent scenarios

        // Detect scenario type
        boolean isCoffeeScenario = strategy.contains("coffee") || strategy.contains("shop") || strategy.contains("home");

        // Set the reward in the most recent TraceEntry
        if (!currentEpisodeDecisions.isEmpty()) {
            for (int i = currentEpisodeDecisions.size() - 1; i >= 0; i--) {
                TraceEntry entry = currentEpisodeDecisions.get(i);
                if ("root".equals(entry.trigger) && entry.reward == 0.0) {
                    entry.reward = reward;
                    break;
                }
            }
        }

        // Compute counterfactual regrets immediately (like RPS in the article)
        InformationSet infoset = getInformationSet("root");

        if (isCoffeeScenario) {
            // COFFEE SCENARIO: Use dynamic expected rewards based on historical success
            // This tracks ACTUAL performance, not theoretical probabilities
            updateHistoricalPerformance(strategy, reward);

            System.out.println("[CFR-Coffee] " + strategy + " → reward=" + reward);

            // Compute counterfactual regrets for ALL alternatives based on historical performance
            for (String planName : new String[]{"try_new_shop", "go_regular_shop", "make_at_home"}) {
                // Skip the plan we actually chose
                if (planName.equals(strategy)) continue;

                // Get historical average reward for this plan
                double historicalReward = getHistoricalAverage(planName);

                // CFR regret formula: regret = historical_avg(alt) - actual(chosen)
                // Positive regret means "Historically, this alternative performs better"
                double regret = historicalReward - reward;

                // Only track positive regrets (we regret not choosing better options)
                if (regret > 0) {
                    double currentRegret = infoset.cumulativeRegret.getOrDefault(planName, 0.0);
                    infoset.cumulativeRegret.put(planName, currentRegret + regret);

                    System.out.println(String.format("  Regret(%s) = %.2f - %.1f = %.3f (cumulative: %.3f)",
                        planName, historicalReward, reward, regret, currentRegret + regret));
                }
            }
        } else {
            // BRIDGE SCENARIO: Use existing logic
            int strategyIdx = bridgeActionToIndex(strategy);
            if (strategyIdx < 0) {
                System.out.println("[Bridge-CFR] Invalid strategy: " + strategy);
                return;
            }
            System.out.println("[Bridge] Strategy=" + strategy + ", Reward=" + reward);
        }

        // Add to total episode reward
        totalEpisodeReward += reward;
    }

    // ==================== HISTORICAL PERFORMANCE TRACKING ====================

    /** Track historical performance for each plan */
    private Map<String, PlanStats> planStats = new HashMap<>();

    /** Statistics for a single plan */
    private static class PlanStats {
        int successCount = 0;
        int failureCount = 0;
        double totalReward = 0.0;
        int attempts = 0;

        double getAverageReward() {
            return attempts == 0 ? 0.0 : totalReward / attempts;
        }

        double getSuccessRate() {
            return attempts == 0 ? 0.0 : (double) successCount / attempts;
        }
    }

    /** Update historical performance for a plan */
    private void updateHistoricalPerformance(String plan, double reward) {
        PlanStats stats = planStats.computeIfAbsent(plan, k -> new PlanStats());
        stats.attempts++;
        stats.totalReward += reward;
        if (reward > 0) stats.successCount++;
        else if (reward < 0) stats.failureCount++;
    }

    /** Get historical average reward for a plan */
    private double getHistoricalAverage(String plan) {
        PlanStats stats = planStats.get(plan);
        if (stats == null || stats.attempts == 0) {
            // Return theoretical expected reward if no data
            switch (plan) {
                case "try_new_shop": return 0.2;     // 60% success
                case "go_regular_shop": return 0.7;  // 85% success
                case "make_at_home": return 0.9;     // 95% success
                default: return 0.0;
            }
        }
        return stats.getAverageReward();
    }

    /**
     * Convert bridge strategy name to index.
     */
    private int bridgeActionToIndex(String strategy) {
        for (int i = 0; i < BRIDGE_ACTIONS.length; i++) {
            if (BRIDGE_ACTIONS[i].equalsIgnoreCase(strategy)) {
                return i;
            }
        }
        return -1;
    }

    /**
     * Update personality based on RPS (Rock-Paper-Scissors) regrets.
     *
     * Note: Currently delegates to bridge scenario as fallback.
     * RPS-specific personality updates can be added here when needed.
     *
     * The RPS cumulative regrets are tracked in rpsCumulativeRegret,
     * but personality updates for RPS scenarios use the same logic as bridge.
     */
    private void updatePersonalityFromRPSRegret() {
        // RPS personality updates use the same bridge logic
        // (both scenarios track cautious/bold traits)
        updatePersonalityFromBridgeRegret();
    }

    /**
     * Update personality based on Coffee Decision CFR regrets.
     *
     * COFFEE SCENARIO:
     * - try_new_shop:    bold(0.8), curious(0.7), cautious(0.2) → 60% success
     * - go_regular_shop: cautious(0.8), bold(0.2), curious(0.3) → 85% success
     * - make_at_home:    cautious(0.9), curious(0.1), bold(0.1) → 95% success
     *
     * CFR Learning: Agent discovers that CAUTIOUS leads to more success!
     */
    private void updatePersonalityFromCoffeeRegret() {
        System.out.println("\n========== CFR: COFFEE DECISION SCENARIO ==========");

        // Plan trait profiles (what traits each plan uses)
        Map<String, Map<String, Double>> planTraits = new HashMap<>();
        planTraits.put("try_new_shop",    Map.of("bold", 0.8, "curious", 0.7, "cautious", 0.2));
        planTraits.put("go_regular_shop", Map.of("cautious", 0.8, "bold", 0.2, "curious", 0.3));
        planTraits.put("make_at_home",    Map.of("cautious", 0.9, "curious", 0.1, "bold", 0.1));

        // Expected success rates (what would happen on average)
        Map<String, Double> expectedReward = new HashMap<>();
        expectedReward.put("try_new_shop",    0.6 * 1.0 + 0.4 * (-1.0));  // 60% success → 0.2
        expectedReward.put("go_regular_shop", 0.85 * 1.0 + 0.15 * (-1.0)); // 85% success → 0.7
        expectedReward.put("make_at_home",    0.95 * 1.0 + 0.05 * (-1.0)); // 95% success → 0.9

        // Aggregate regrets from all decisions in this episode
        Map<String, Double> totalRegret = new HashMap<>();
        totalRegret.put("try_new_shop", 0.0);
        totalRegret.put("go_regular_shop", 0.0);
        totalRegret.put("make_at_home", 0.0);

        int regretCount = 0;
        for (InformationSet infoset : informationSets.values()) {
            for (Map.Entry<String, Double> entry : infoset.cumulativeRegret.entrySet()) {
                String plan = entry.getKey();
                double regret = entry.getValue();
                totalRegret.put(plan, totalRegret.getOrDefault(plan, 0.0) + regret);
                regretCount++;
            }
        }

        // Print regrets (like in the article's table)
        System.out.println("Cumulative Regrets:");
        System.out.println("  try_new_shop:    " + String.format("%.3f", totalRegret.get("try_new_shop")));
        System.out.println("  go_regular_shop: " + String.format("%.3f", totalRegret.get("go_regular_shop")));
        System.out.println("  make_at_home:    " + String.format("%.3f", totalRegret.get("make_at_home")));

        // Compute personality updates via regret matching
        // (like strategy update in article: σ(a) = [R(a)]+ / Σ[R(a')]+)
        Map<String, Double> traitGradients = new HashMap<>();
        traitGradients.put("bold", 0.0);
        traitGradients.put("curious", 0.0);
        traitGradients.put("cautious", 0.0);

        // Sum positive regrets only
        double totalPositiveRegret = 0.0;
        for (Map.Entry<String, Double> entry : totalRegret.entrySet()) {
            if (entry.getValue() > 0) {
                totalPositiveRegret += entry.getValue();
            }
        }

        if (totalPositiveRegret > 0.001) {
            System.out.println("\nPersonality Updates (Regret Matching):");

            // For each plan with positive regret, update personality toward its traits
            for (Map.Entry<String, Double> entry : totalRegret.entrySet()) {
                String plan = entry.getKey();
                double regret = entry.getValue();

                if (regret > 0) {
                    double regretWeight = regret / totalPositiveRegret;
                    Map<String, Double> traits = planTraits.get(plan);

                    System.out.println("  Plan '" + plan + "' (regret=" + String.format("%.3f", regret) +
                        ", weight=" + String.format("%.1f%%", regretWeight * 100) + ")");

                    // Update each trait toward this plan's trait value
                    for (Map.Entry<String, Double> traitEntry : traits.entrySet()) {
                        String traitName = traitEntry.getKey();
                        double traitValue = traitEntry.getValue();

                        // Gradient = regretWeight * (traitValue - currentPersonality)
                        double currentPers = personality.getOrDefault(traitName, 0.5);
                        double gradient = regretWeight * (traitValue - currentPers);

                        traitGradients.put(traitName, traitGradients.get(traitName) + gradient);

                        System.out.println("    " + traitName + ": plan_value=" + String.format("%.2f", traitValue) +
                            ", current=" + String.format("%.2f", currentPers) + ", gradient=" + String.format("%.3f", gradient));
                    }
                }
            }

            // Apply updates with learning rate
            System.out.println("\nApplying personality updates (learning_rate=" + cfrLearningRate + "):");
            for (String trait : traitGradients.keySet()) {
                double gradient = traitGradients.get(trait);
                if (Math.abs(gradient) > 0.001) {
                    double oldValue = personality.getOrDefault(trait, 0.5);
                    double newValue = oldValue + cfrLearningRate * gradient;
                    newValue = Math.max(0.0, Math.min(1.0, newValue));

                    personality.put(trait, newValue);

                    System.out.println("  " + trait + ": " + String.format("%.3f", oldValue) +
                        " → " + String.format("%.3f", newValue));
                }
            }
        } else {
            System.out.println("\nNo positive regrets - personality unchanged");
        }

        System.out.println("====================================================\n");
    }

    /**
     * Update personality based on Bridge Crossing CFR regrets.
     */
    private void updatePersonalityFromBridgeRegret() {
        Map<String, Double> traitUpdates = new HashMap<>();
        traitUpdates.put("cautious", 0.0);
        traitUpdates.put("bold", 0.0);

        // Aggregate regrets from ALL information sets (unified CFR)
        for (InformationSet infoset : informationSets.values()) {
            for (Map.Entry<String, Double> entry : infoset.cumulativeRegret.entrySet()) {
                String action = entry.getKey();
                double regret = entry.getValue();

                if (regret > 0) {
                    switch (action) {
                        case "cross_carefully":
                        case "carefully":
                            traitUpdates.put("cautious", traitUpdates.get("cautious") + regret);
                            break;
                        case "cross_boldly":
                        case "boldly":
                            traitUpdates.put("bold", traitUpdates.get("bold") + regret);
                            break;
                        case "test_steps":
                            traitUpdates.put("cautious", traitUpdates.get("cautious") + regret * 0.7);
                            traitUpdates.put("bold", traitUpdates.get("bold") + regret * 0.3);
                            break;
                        case "find_alternative":
                        case "alternative":
                            traitUpdates.put("cautious", traitUpdates.get("cautious") + regret * 0.5);
                            traitUpdates.put("bold", traitUpdates.get("bold") + regret * 0.5);
                            break;
                        case "wait_conditions":
                        case "wait":
                            traitUpdates.put("cautious", traitUpdates.get("cautious") + regret * 0.8);
                            traitUpdates.put("bold", traitUpdates.get("bold") + regret * 0.2);
                            break;
                    }
                }
            }
        }

        double netBias = traitUpdates.get("bold") - traitUpdates.get("cautious");

        if (Math.abs(netBias) > 0.001) {
            double oldCautious = personality.getOrDefault("cautious", 0.5);
            double oldBold = personality.getOrDefault("bold", 0.5);

            double change = netBias * cfrLearningRate * 0.5;
            double newCautious = oldCautious - change;
            double newBold = oldBold + change;

            newCautious = Math.max(0.0, Math.min(1.0, newCautious));
            newBold = Math.max(0.0, Math.min(1.0, newBold));

            personality.put("cautious", newCautious);
            personality.put("bold", newBold);

            System.out.println(String.format("[Bridge-CFR] Personality: cautious=%.3f->%.3f, bold=%.3f->%.3f (bias=%.3f)",
                oldCautious, newCautious, oldBold, newBold, netBias));
        }
    }

    /** Get action index (0=rock, 1=paper, 2=scissors) */
    private int actionToIndex(String action) {
        if (action == null) return -1;
        switch (action.toLowerCase()) {
            case "rock": return 0;
            case "paper": return 1;
            case "scissors": return 2;
            default: return -1;
        }
    }

    /** Get current RPS cumulative regrets (for stats) */
    public Map<String, Double> getRPSCumulativeRegrets() {
        return new HashMap<>(rpsCumulativeRegret);
    }

    /** Get current Coffee Decision cumulative regrets (for visualization) */
    public Map<String, Double> getCoffeeCumulativeRegrets() {
        Map<String, Double> regrets = new HashMap<>();
        regrets.put("try_new_shop", 0.0);
        regrets.put("go_regular_shop", 0.0);
        regrets.put("make_at_home", 0.0);

        // Aggregate from all information sets
        for (InformationSet infoset : informationSets.values()) {
            for (Map.Entry<String, Double> entry : infoset.cumulativeRegret.entrySet()) {
                String plan = entry.getKey();
                double regret = entry.getValue();
                regrets.put(plan, regrets.getOrDefault(plan, 0.0) + regret);
            }
        }
        return regrets;
    }

    /** Apply mood effects from plan annotation (called after plan execution) */
    public void applyMoodEffects( Literal effectList ) throws NoValueException {
        updateDynTemper( effectList );
    }

    // ==================== PERSONALITY PERSISTENCE ====================

    /** Save personality to JSON file */
    private void savePersonality() {
        try {
            StringBuilder json = new StringBuilder();
            json.append("{\n");
            json.append("  \"personality\": {\n");
            int i = 0;
            for ( Map.Entry<String, Double> entry : personality.entrySet() ) {
                double val = Math.round( entry.getValue() * 1000.0 ) / 1000.0;
                json.append("    \"").append( entry.getKey() ).append("\": ")
                    .append( val );  // Use rounded value for clean JSON
                if ( i < personality.size() - 1 ) json.append(",");
                json.append("\n");
                i++;
            }
            json.append("  },\n");
            json.append("  \"mood\": {\n");
            i = 0;
            for ( Map.Entry<String, Double> entry : mood.entrySet() ) {
                double val = Math.round( entry.getValue() * 1000.0 ) / 1000.0;
                json.append("    \"").append( entry.getKey() ).append("\": ")
                    .append( val );  // Use rounded value for clean JSON
                if ( i < mood.size() - 1 ) json.append(",");
                json.append("\n");
                i++;
            }
            json.append("  }\n");
            json.append("}\n");

            Files.writeString( Path.of( PERSONALITY_FILE ), json.toString() );
            System.out.println( "[PERSIST] Personality saved to " + PERSONALITY_FILE );
        } catch ( IOException e ) {
            System.err.println( "[PERSIST] Failed to save personality: " + e.getMessage() );
        }
    }

    /** Load personality from JSON file (call this before constructor if needed) */
    public static Map<String, Object> loadPersonalityFromFile() {
        try {
            File f = new File( PERSONALITY_FILE );
            if ( !f.exists() ) {
                System.out.println( "[PERSIST] No saved personality found, using defaults" );
                return null;
            }

            String content = Files.readString( Path.of( PERSONALITY_FILE ) );
            System.out.println( "[PERSIST] Loaded personality from " + PERSONALITY_FILE );
            System.out.println( content );

            // Simple JSON parser for our format
            Map<String, Object> result = new HashMap<>();
            result.put( "personality", new HashMap<String, Double>() );
            result.put( "mood", new HashMap<String, Double>() );

            String[] lines = content.split( "\n" );
            String currentSection = null;

            for ( String line : lines ) {
                line = line.trim();
                if ( line.contains( "\"personality\":" ) ) {
                    currentSection = "personality";
                } else if ( line.contains( "\"mood\":" ) ) {
                    currentSection = "mood";
                } else if ( line.contains( ": " ) && currentSection != null ) {
                    // Parse "key": value
                    String[] parts = line.split( "\": " );
                    if ( parts.length == 2 ) {
                        String key = parts[0].replace( "\"", "" ).trim();
                        double value = Double.parseDouble( parts[1].replace( ",", "" ).trim() );
                        ( (Map<String, Double>) result.get( currentSection ) ).put( key, value );
                    }
                }
            }

            return result;
        } catch ( Exception e ) {
            System.err.println( "[PERSIST] Failed to load personality: " + e.getMessage() );
            return null;
        }
    }

    /** Get personality file name for use in VesnaAgent */
    public static String getPersonalityFile() {
        return PERSONALITY_FILE;
    }

    /** Get current mood values */
    public Map<String, Double> getMood() {
        return new HashMap<>(mood);
    }

    /** Get total reward for current episode */
    public double getTotalEpisodeReward() {
        return totalEpisodeReward;
    }

    // ==================== PRIVATE HELPERS ====================

    private int getWeightedRandomIdx( List<Double> weights ) {
        // Use softmax to convert weights to probabilities (same as computeActionProbabilities)
        double[] probs = computeActionProbabilities( weights );

        // Compute cumulative probabilities
        double[] cumulative = new double[weights.size()];
        double total = 0.0;
        for ( int i = 0; i < weights.size(); i++ ) {
            total += probs[i];
            cumulative[i] = total;
        }

        // Random roll in [0, 1]
        double roll = dice.nextDouble( 0.0, 1.0 );

        // Debug output
        StringBuilder sb = new StringBuilder( "[RANDOM] roll=" ).append( String.format("%.3f", roll ) );
        sb.append( " cumulative=" );
        for ( int i = 0; i < cumulative.length; i++ ) {
            sb.append( String.format("%.3f", cumulative[i] ) );
            if ( i < cumulative.length - 1 ) sb.append( ", " );
        }
        System.out.println( sb.toString() );

        // Find which bucket the roll falls into
        for ( int i = 0; i < cumulative.length; i++ ) {
            if ( roll < cumulative[i] ) {
                return i;
            }
        }
        return weights.size() - 1;  // Fallback to last
    }

    private int getMostSimilarIdx( List<Double> weights ) {
        double min = Double.MAX_VALUE;
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
            if ( personality.keySet().contains( effect.getFunctor().toString() ) && !effect.hasAnnot( createLiteral( "mood" ) ) )
                throw new IllegalArgumentException( "You used a Personality trait in the post-effects! Use only mood traits. In case of ambiguous name use the annotation [mood]." );
            if ( mood.get( effect.getFunctor().toString() ) == null )
                continue;
            double moodValue = mood.get( effect.getFunctor().toString() );
            try {
                double effectValue = ( double ) ( ( NumberTerm ) effect.getTerm( 0 ) ).solve();
                if ( effectValue < - 1.0 || effectValue > 1.0 )
                    throw new IllegalArgumentException("Effect value out of range: " + effectValue + ". It should be between [-1,1].");
                if ( moodValue + effectValue > 1.0 )
                    mood.put( effect.getFunctor().toString(), 1.0 );
                else if ( moodValue + effectValue < -1.0 )
                    mood.put( effect.getFunctor().toString(), 0.0 );  // Original: sets to 0.0 (kept for compatibility)
                else
                    mood.put( effect.getFunctor().toString(), moodValue + effectValue );
                System.out.println( "[TEMPER] Mood update: " + effect.getFunctor() + " " + String.format("%.2f", moodValue) + " -> " + String.format("%.2f", mood.get(effect.getFunctor().toString())) );
            } catch ( NoValueException nve ) {
                throw new NoValueException( "One of the plans has a misspelled annotation" );
            }
        }
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append( "[TEMPER] Personality: " );
        personality.forEach( (k, v) -> sb.append( k + "=" + String.format("%.2f", v) + " " ) );
        sb.append( "| Mood: " );
        mood.forEach( (k, v) -> sb.append( k + "=" + String.format("%.2f", v) + " " ) );
        return sb.toString();
    }

}
