package vesna;

import java.util.HashMap;
import java.util.Map;

/**
 * Configuration for the workplace help-seeking scenario.
 *
 * <p>Declares, for each plan the scenario defines, a vector of OCEAN trait
 * annotations in [-1, +1]. These annotations are used by Pro-AgentSpeak(L)'s
 * compatibility measure for plan selection, and by the regret-to-propensity
 * projection for personality learning.</p>
 *
 * <p>The OCEAN dimensions are Openness, Conscientiousness, Extraversion,
 * Agreeableness, Neuroticism. A value of +1 means the plan strongly embodies
 * that trait, -1 the opposite, 0 neutral. Dimensions that are semantically
 * irrelevant for a plan are set to 0.</p>
 */
public class HelpScenarioConfig {

    /** Plan name -> OCEAN profile in [-1, +1]. */
    private static final Map<String, Map<String, Double>> ACTION_TRAITS = new HashMap<>();

    static {
        // ----- Bob: senior developer, moderate reciprocity (static partner) -----
        ACTION_TRAITS.put("help_bob", Map.of(
            "agreeableness",  0.6, "conscientiousness",  0.4,
            "extraversion",   0.0, "openness",          -0.2, "neuroticism", -0.4));
        ACTION_TRAITS.put("decline_bob", Map.of(
            "conscientiousness",  0.6, "agreeableness", -0.6,
            "extraversion",      -0.6, "openness",      -0.6, "neuroticism", -0.8));
        ACTION_TRAITS.put("delay_bob", Map.of(
            "openness",        0.4, "conscientiousness",  0.4,
            "agreeableness",  -0.2, "extraversion",      -0.4, "neuroticism", -0.8));

        // ----- Carol: junior developer, exploitative (CFR-learning partner) -----
        ACTION_TRAITS.put("help_carol", Map.of(
            "agreeableness",      0.8, "neuroticism",   0.6,
            "conscientiousness", -0.6, "extraversion",  0.0, "openness", -0.4));
        ACTION_TRAITS.put("decline_carol", Map.of(
            "conscientiousness",  0.8, "agreeableness", -0.8,
            "extraversion",      -0.8, "openness",      -0.4, "neuroticism", -0.9));
        ACTION_TRAITS.put("teach_carol", Map.of(
            "openness",        0.6, "conscientiousness",  0.2,
            "agreeableness",  -0.2, "extraversion",      -0.2, "neuroticism", -0.6));

        // ----- Dave: product manager, highly reciprocal (static partner) -----
        ACTION_TRAITS.put("help_dave", Map.of(
            "openness",           0.4, "extraversion",    0.2,
            "conscientiousness",  0.0, "agreeableness",   0.0, "neuroticism", -0.8));
        ACTION_TRAITS.put("decline_dave", Map.of(
            "conscientiousness",  0.2, "agreeableness", -0.6,
            "extraversion",      -0.8, "openness",      -0.6, "neuroticism", -0.8));
        ACTION_TRAITS.put("suggest_dave", Map.of(
            "openness",        0.4, "conscientiousness",  0.4,
            "agreeableness",  -0.2, "extraversion",      -0.4, "neuroticism", -0.8));

        // ----- Alice's responses when Carol (the CFR agent) asks for help -----
        ACTION_TRAITS.put("help_alice", Map.of(
            "agreeableness",   0.8, "conscientiousness",  0.2,
            "extraversion",    0.0, "openness",          -0.2, "neuroticism", -0.4));
        ACTION_TRAITS.put("decline_alice", Map.of(
            "conscientiousness",  0.6, "agreeableness", -0.6,
            "extraversion",      -0.6, "openness",      -0.4, "neuroticism", -0.8));
        ACTION_TRAITS.put("teach_alice", Map.of(
            "openness",        0.6, "conscientiousness",  0.2,
            "agreeableness",   0.0, "extraversion",      -0.2, "neuroticism", -0.6));
    }

    /** Returns the OCEAN annotation of a plan, or null if the plan is unknown. */
    public static Map<String, Double> getActionTraits(String action) {
        return ACTION_TRAITS.get(action);
    }

    /** Returns all plan-trait annotations (unmodifiable view is not enforced). */
    public static Map<String, Map<String, Double>> getAllActionTraits() {
        return ACTION_TRAITS;
    }

    /** Returns the plan names available to a given social partner. */
    public static String[] getActionsForPerson(String person) {
        switch (person.toLowerCase()) {
            case "bob":   return new String[]{"help_bob",   "decline_bob",   "delay_bob"};
            case "carol": return new String[]{"help_alice", "decline_alice", "teach_alice"};
            case "dave":  return new String[]{"help_dave",  "decline_dave",  "suggest_dave"};
            default:      return new String[]{};
        }
    }

    /**
     * Initialises the behavioural memory for the three colleagues.
     * Bob and Dave are static (no CFR); Carol is CFR-learning with an
     * initially exploitative profile.
     */
    public static void initBehavioralMemory(BehavioralMemory memory) {
        // Bob: reliability 0.6, innate reciprocity 0.4.
        memory.addPerson("bob", "Bob", 0.6, 0.4);

        // Carol: exploitative (low A, low innate reciprocity). The CFR loop
        // will drive her personality away from this starting point as Alice's
        // declining behaviour trains her toward reciprocation.
        //   Initial personality in [-1, +1]: O=+0.2, C=-0.2, E=+0.2, A=-0.4, N=0.0
        memory.addPersonWithPersonality(
            "carol", "Carol",
            /* reliability */        0.2,
            /* innate reciprocity */ 0.1,
            /* openness */           0.2,
            /* conscientiousness */ -0.2,
            /* extraversion */       0.2,
            /* agreeableness */     -0.4,
            /* neuroticism */        0.0);

        // Dave: reliability 0.8, innate reciprocity 0.9.
        memory.addPerson("dave", "Dave", 0.8, 0.9);

        System.out.println("[BEHAVIORAL MEMORY] Initialised:");
        System.out.println("  Bob:   static  (reliability=0.6, reciprocity=0.4)");
        System.out.println("  Carol: CFR     (A=-0.4 exploitative, reciprocity=0.1)");
        System.out.println("  Dave:  static  (reliability=0.8, reciprocity=0.9)");
    }
}
