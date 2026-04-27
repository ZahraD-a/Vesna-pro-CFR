package vesna;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;
import java.util.ArrayList;
import java.util.List;

/**
 * Tracks per-colleague relationship dynamics for CFR personality learning.
 *
 * Each colleague has a PersonMemory tracking reciprocity, exploitation,
 * and relationship quality. These values are used by record_outcome
 * to compute enhanced rewards that create reward divergence from
 * initially uniform base rewards.
 *
 * <h3>Carol's CFR state lives here (not in Temper)</h3>
 * Carol is an <i>observational-CFR</i> learner: her regret is over the action
 * she attributes to Alice, with a fixed-ratio counterfactual on Alice's
 * untaken actions (see {@link PersonMemory#recordDecisionOutcome}). At episode
 * end, {@link PersonMemory#updatePersonalityFromRegret} projects the regret
 * vector onto Carol's OCEAN traits via the same regret-matching kernel Alice
 * uses in {@code Temper.updatePersonalityFromCFR}, but with action-trait
 * profiles defined locally for Carol's three internal actions
 * ({help, decline, reciprocate}).
 *
 * <p>This is the single source of truth for Carol's personality; the previous
 * Temper-side scaffolding has been removed.
 *
 * EXTENSION: Carol (and optionally other colleagues) now have:
 * - OCEAN personality traits that evolve via CFR
 * - Response plans: help_colleague, decline_colleague, reciprocate_colleague
 * - Regret tracking and personality updates
 */
public class BehavioralMemory {

    private final Map<String, PersonMemory> memory = new HashMap<>();

    /** Memory for a single person. */
    public static class PersonMemory {
        public final String name;
        public double relationshipScore;
        public double reliabilityScore;
        public double reciprocityRatio;

        public int timesHelped = 0;
        public int timesAsked = 0;
        public int timesTheyHelpedYou = 0;

        public boolean isExploitative = false;
        public boolean isAppreciative = false;
        public boolean isReciprocal = false;

        // Innate reciprocity tendency (probability they help you back)
        public final double reliability;
        public final double reciprocity;
        /** Adaptive reciprocity: starts equal to innate, changes based on
         *  observed agent behaviour. This is what actually drives Bernoulli trials. */
        public double adaptedReciprocity;
        
        // ===== CFR PERSONALITY LEARNING EXTENSION =====
        /** OCEAN personality traits (only for Carol in current version) */
        public Map<String, Double> personality = new HashMap<>();
        
        /** Cumulative regret for each action (help, decline, reciprocate) */
        public Map<String, Double> cumulativeRegret = new HashMap<>();
        // Per-action running totals used to estimate the COMA-style
        // counterfactual baseline for unchosen actions (mirrors the
        // historical-mean baseline in Temper.getHistoricalAverage).
        public Map<String, Double>  historicalRewardSum   = new HashMap<>();
        public Map<String, Integer> historicalRewardCount = new HashMap<>();
        
        /** Strategy sum for regret matching */
        public Map<String, Double> strategySum = new HashMap<>();
        
        /** Action count for normalization */
        public int actionCount = 0;
        
        /** CFR step size for Carol's personality update (matches Alice's 0.005 on [-1,+1]). */
        private static final double CFR_LEARNING_RATE = 0.005;
        
        /** Whether this agent learns via CFR (Carol = true, Bob/Dave = false) */
        public boolean learnsViaCFR;
        
        /** List of decision traces for CFR updates */
        public List<String> lastDecisionTrace = new ArrayList<>();

        public PersonMemory(String name, double reliability, double reciprocity) {
            this.name = name;
            this.relationshipScore = 0.5;
            this.reliabilityScore = reliability;
            this.reciprocityRatio = 0.5;  // Start neutral — agent must learn from experience
            this.reliability = reliability;
            this.reciprocity = reciprocity;  // Innate tendency (hidden, drives stochastic outcomes)
            this.adaptedReciprocity = reciprocity;
            this.learnsViaCFR = false;  // Default: no CFR
            
            // Initialize CFR structures
            this.cumulativeRegret.put("help", 0.0);
            this.cumulativeRegret.put("decline", 0.0);
            this.cumulativeRegret.put("reciprocate", 0.0);
            this.strategySum.put("help", 1.0);
            this.strategySum.put("decline", 1.0);
            this.strategySum.put("reciprocate", 1.0);
        }
        
        /**
         * Constructor for Carol: includes OCEAN personality and CFR learning.
         */
        public PersonMemory(String name, double reliability, double reciprocity, 
                           boolean learnsViaCFR, 
                           double openness, double conscientiousness, double extraversion,
                           double agreeableness, double neuroticism) {
            this(name, reliability, reciprocity);
            this.learnsViaCFR = learnsViaCFR;
            
            if (learnsViaCFR) {
                // Initialize OCEAN personality traits
                this.personality.put("openness", openness);
                this.personality.put("conscientiousness", conscientiousness);
                this.personality.put("extraversion", extraversion);
                this.personality.put("agreeableness", agreeableness);
                this.personality.put("neuroticism", neuroticism);
                
                System.out.println("[INIT] " + name + " initialized with personality: "
                    + "O=" + String.format("%.2f", openness)
                    + " C=" + String.format("%.2f", conscientiousness)
                    + " E=" + String.format("%.2f", extraversion)
                    + " A=" + String.format("%.2f", agreeableness)
                    + " N=" + String.format("%.2f", neuroticism));
            }
        }

        /**
         * Update memory after an interaction.
         * Whether they reciprocate is probabilistic based on their innate tendency.
         */
        public void update(boolean helped, Random dice) {
            timesAsked++;
            if (helped) {
                timesHelped++;
                // Did they reciprocate? Uses adapted reciprocity so colleague responds to agent behaviour
                boolean reciprocated = dice.nextDouble() < adaptedReciprocity;
                if (reciprocated) {
                    timesTheyHelpedYou++;
                    relationshipScore = Math.min(1.0, relationshipScore + 0.05);
                } else {
                    relationshipScore = Math.max(0.0, relationshipScore - 0.02);
                }
            }

            // Standard cumulative ratio — conservative trust recovery
            if (timesHelped > 0) {
                reciprocityRatio = (double) timesTheyHelpedYou / timesHelped;
            }

            // Update pattern flags (only after enough data)
            isExploitative = reciprocityRatio < 0.2 && timesAsked > 3;
            isAppreciative = relationshipScore > 0.7;
            isReciprocal = reciprocityRatio > 0.5;
        }

        /**
         * Colleague adapts reciprocity based on what the agent did this cycle.
         * If the agent declined: colleague increases reciprocity slightly
         *   (incentive to win cooperation back).
         * If the agent helped: slow natural drift back toward innate tendency.
         *
         * @param agentDeclined true if the agent declined this cycle
         */
        public void adaptReciprocity(boolean agentDeclined) {
            if (agentDeclined) {
                // Proportional adaptation: increment scales with remaining capacity to cap.
                // Creates smooth S-curve that asymptotically approaches 0.85 over full timeline.
                // Base rate 0.012 allows faster learning than 0.008.
                double remainingCapacity = 0.85 - adaptedReciprocity;
                adaptedReciprocity += 0.012 * remainingCapacity;
            } else {
                adaptedReciprocity = adaptedReciprocity
                    + 0.003 * (reciprocity - adaptedReciprocity);
            }
            System.out.println("[ADAPT] " + name
                + " reciprocity: " + String.format("%.3f", adaptedReciprocity)
                + " (innate=" + String.format("%.2f", reciprocity) + ")"
                + (agentDeclined ? " [agent declined]" : " [agent helped]"));
        }
        
        /**
         * For CFR-learning colleagues like Carol:
         * Select an action (help, decline, reciprocate) based on current personality
         * and cumulative regret using regret matching.
         * 
         * Returns the selected action.
         */
        public String selectAction(Random dice) {
            if (!learnsViaCFR) {
                // Non-learning colleagues: probabilistic based on adaptedReciprocity
                double r = dice.nextDouble();
                if (r < adaptedReciprocity) {
                    return "reciprocate";  // Help back
                } else {
                    return "decline";  // Don't help
                }
            }
            
            // CFR-learning colleagues (Carol): use regret matching
            String[] actions = {"help", "decline", "reciprocate"};
            
            // Compute positive regrets
            double[] positiveRegrets = new double[3];
            double totalPositiveRegret = 0.0;
            for (int i = 0; i < 3; i++) {
                double regret = cumulativeRegret.get(actions[i]);
                positiveRegrets[i] = Math.max(0.0, regret);
                totalPositiveRegret += positiveRegrets[i];
            }
            
            // Regret matching: normalize to probability distribution
            double[] strategy = new double[3];
            if (totalPositiveRegret > 0.0) {
                for (int i = 0; i < 3; i++) {
                    strategy[i] = positiveRegrets[i] / totalPositiveRegret;
                }
            } else {
                // Uniform if no positive regret
                for (int i = 0; i < 3; i++) {
                    strategy[i] = 1.0 / 3.0;
                }
            }
            
            // Select action via multinomial sampling
            double r = dice.nextDouble();
            double cumulative = 0.0;
            for (int i = 0; i < 3; i++) {
                cumulative += strategy[i];
                if (r < cumulative) {
                    lastDecisionTrace.add(actions[i]);
                    return actions[i];
                }
            }
            
            lastDecisionTrace.add("reciprocate");  // Fallback
            return "reciprocate";
        }
        
        /**
         * Record the outcome of Carol's decision and compute regrets.
         * Called at the end of each episode for CFR update (follows Alice's pattern).
         * 
         * @param actionTaken The action Carol chose this episode
         * @param reward The reward Carol received
         */
        /** Mean reward observed historically for an action; 0.0 if never tried. */
        public double getHistoricalReward(String action) {
            int n = historicalRewardCount.getOrDefault(action, 0);
            if (n == 0) return 0.0;
            return historicalRewardSum.getOrDefault(action, 0.0) / n;
        }

        public void recordDecisionOutcome(String actionTaken, double reward) {
            if (!learnsViaCFR) return;

            String[] actions = {"help", "decline", "reciprocate"};

            // Update the running mean reward of the chosen action.
            historicalRewardSum.merge(actionTaken, reward, Double::sum);
            historicalRewardCount.merge(actionTaken, 1, Integer::sum);

            // Counterfactual regret with COMA-style historical-mean baseline
            // (mirrors Temper.recordHelpOutcome). For each action a:
            //   r_t(a) = E_hist[r | a] - reward          if a != actionTaken
            //   r_t(a) = 0                               if a == actionTaken
            // Cumulative regret accumulator follows Hart & Mas-Colell (2000).
            for (String action : actions) {
                if (action.equals(actionTaken)) continue;
                double counterfactualReward = getHistoricalReward(action);
                double instantRegret = counterfactualReward - reward;
                cumulativeRegret.merge(action, instantRegret, Double::sum);
            }

            actionCount++;

            // Per-interaction trace (one row per Carol CFR iteration).
            try {
                int episode = vesna.via.cfr_episode.getCurrentEpisode();
                vesna.personality.PolicyLogger.logCarolTrace(
                    episode, actionTaken, reward, cumulativeRegret);
            } catch (Throwable ignored) { /* logging must never break sim */ }

            System.out.println("[CFR] " + name + " action=" + actionTaken 
                + " reward=" + String.format("%.2f", reward)
                + " cumRegret: help=" + String.format("%.2f", cumulativeRegret.get("help"))
                + " decline=" + String.format("%.2f", cumulativeRegret.get("decline"))
                + " reciprocate=" + String.format("%.2f", cumulativeRegret.get("reciprocate")));
        }
        
        /**
         * Update Carol's personality based on accumulated regrets.
         * Called at the end of each episode (or every N episodes).
         */
        /**
         * Project Carol's cumulative regrets onto her OCEAN personality vector.
         *
         * <p>Identical in structure to Alice's CFR update in {@link Temper}:
         * regret matching gives a weight sigma(a) on each action a, and the
         * personality gradient for trait l is the sigma-weighted pull of each
         * action's trait profile toward the current personality. Trait values
         * stay in [-1, +1].</p>
         *
         * <p>Carol's three internal actions are "help" (reciprocate with help),
         * "decline" (refuse), and "reciprocate" (mentor in return). Their trait
         * profiles below mirror the corresponding plan annotations Alice uses
         * for the same decisions, rescaled into [-1, +1].</p>
         */
        public void updatePersonalityFromRegret() {
            if (!learnsViaCFR || personality.isEmpty()) return;

            // Action trait profiles in [-1, +1] for Carol's three decision options.
            Map<String, Map<String, Double>> profiles = new HashMap<>();
            profiles.put("help", Map.of(
                "openness",         -0.2, "conscientiousness",  0.2,
                "extraversion",      0.0, "agreeableness",      0.8, "neuroticism", -0.4));
            profiles.put("decline", Map.of(
                "openness",         -0.4, "conscientiousness",  0.6,
                "extraversion",     -0.6, "agreeableness",     -0.6, "neuroticism", -0.8));
            profiles.put("reciprocate", Map.of(
                "openness",          0.6, "conscientiousness",  0.2,
                "extraversion",     -0.2, "agreeableness",      0.0, "neuroticism", -0.6));

            // Total positive cumulative regret (denominator of regret matching).
            double totalPositive = 0.0;
            for (double r : cumulativeRegret.values()) {
                if (r > 0) totalPositive += r;
            }
            if (totalPositive < 1e-6) return;

            // Accumulate the regret-weighted gradient per trait.
            Map<String, Double> gradients = new HashMap<>();
            for (String trait : personality.keySet()) gradients.put(trait, 0.0);

            for (Map.Entry<String, Double> entry : cumulativeRegret.entrySet()) {
                double regret = entry.getValue();
                if (regret <= 0) continue;
                double weight = regret / totalPositive;
                Map<String, Double> profile = profiles.get(entry.getKey());
                if (profile == null) continue;
                for (String trait : personality.keySet()) {
                    double target  = profile.getOrDefault(trait, 0.0);
                    double current = personality.get(trait);
                    gradients.merge(trait, weight * (target - current), Double::sum);
                }
            }

            // Apply gradient with clipping to [-1, +1].
            for (String trait : personality.keySet()) {
                double oldValue = personality.get(trait);
                double newValue = oldValue + CFR_LEARNING_RATE * gradients.get(trait);
                newValue = Math.max(-1.0, Math.min(1.0, newValue));
                personality.put(trait, newValue);
            }

            System.out.println("[PERSONALITY UPDATE] " + name
                + " O=" + String.format("%+.3f", personality.get("openness"))
                + " C=" + String.format("%+.3f", personality.get("conscientiousness"))
                + " E=" + String.format("%+.3f", personality.get("extraversion"))
                + " A=" + String.format("%+.3f", personality.get("agreeableness"))
                + " N=" + String.format("%+.3f", personality.get("neuroticism"))
                + " (R_help=" + String.format("%+.2f", cumulativeRegret.getOrDefault("help", 0.0))
                + " R_dec=" + String.format("%+.2f", cumulativeRegret.getOrDefault("decline", 0.0))
                + " R_rec=" + String.format("%+.2f", cumulativeRegret.getOrDefault("reciprocate", 0.0)) + ")");
        }
    }

    /** Add a person to the memory. */
    public void addPerson(String key, String name, double reliability, double reciprocity) {
        memory.put(key, new PersonMemory(name, reliability, reciprocity));
    }
    
    /**
     * Add a person with personality traits and CFR learning (for Carol).
     */
    public void addPersonWithPersonality(String key, String name, double reliability, double reciprocity,
                                         double openness, double conscientiousness, double extraversion,
                                         double agreeableness, double neuroticism) {
        memory.put(key, new PersonMemory(name, reliability, reciprocity, true,
                                         openness, conscientiousness, extraversion, agreeableness, neuroticism));
    }

    /** Update behavioral memory after an interaction. */
    public void update(String person, boolean helped, Random dice) {
        PersonMemory pm = memory.get(person.toLowerCase());
        if (pm != null) {
            pm.update(helped, dice);
            System.out.println("[BEHAVIOR] " + pm.name
                + ": relationship=" + String.format("%.2f", pm.relationshipScore)
                + ", reciprocity=" + String.format("%.2f", pm.reciprocityRatio)
                + ", pattern=" + (pm.isExploitative ? "EXPLOITATIVE"
                    : pm.isReciprocal ? "RECIPROCAL" : "NEUTRAL"));
        }
    }

    /** Get behavioral memory value for a person. */
    public double getValue(String person, String metric) {
        PersonMemory pm = memory.get(person.toLowerCase());
        if (pm == null) return 0.5;

        switch (metric.toLowerCase()) {
            case "relationship": return pm.relationshipScore;
            case "reciprocity": return pm.reciprocityRatio;
            case "reliability": return pm.reliabilityScore;
            case "is_exploitative": return pm.isExploitative ? 1.0 : 0.0;
            case "is_reciprocal": return pm.isReciprocal ? 1.0 : 0.0;
            default: return 0.5;
        }
    }

    /** Check if memory has been initialized. */
    public boolean isEmpty() {
        return memory.isEmpty();
    }

    /** Return PersonMemory for a given key, or null if not found. */
    public PersonMemory getPersonMemory(String key) {
        return memory.get(key.toLowerCase());
    }
}
