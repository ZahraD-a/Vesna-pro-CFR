package vesna;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

/**
 * Tracks per-colleague relationship dynamics for CFR personality learning.
 *
 * Each colleague has a PersonMemory tracking reciprocity, exploitation,
 * and relationship quality. These values are used by record_outcome
 * to compute enhanced rewards that create reward divergence from
 * initially uniform base rewards.
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

        public PersonMemory(String name, double reliability, double reciprocity) {
            this.name = name;
            this.relationshipScore = 0.5;
            this.reliabilityScore = reliability;
            this.reciprocityRatio = 0.5;  // Start neutral — agent must learn from experience
            this.reliability = reliability;
            this.reciprocity = reciprocity;  // Innate tendency (hidden, drives stochastic outcomes)
            this.adaptedReciprocity = reciprocity;
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

            // Update observed reciprocity from data
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
                adaptedReciprocity = Math.min(0.85, adaptedReciprocity + 0.02);
            } else {
                adaptedReciprocity = adaptedReciprocity
                    + 0.003 * (reciprocity - adaptedReciprocity);
            }
            System.out.println("[ADAPT] " + name
                + " reciprocity: " + String.format("%.3f", adaptedReciprocity)
                + " (innate=" + String.format("%.2f", reciprocity) + ")"
                + (agentDeclined ? " [agent declined]" : " [agent helped]"));
        }
    }

    /** Add a person to the memory. */
    public void addPerson(String key, String name, double reliability, double reciprocity) {
        memory.put(key, new PersonMemory(name, reliability, reciprocity));
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
