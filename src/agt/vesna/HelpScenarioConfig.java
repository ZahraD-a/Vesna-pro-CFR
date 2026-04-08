package vesna;

import java.util.HashMap;
import java.util.Map;

/**
 * Configuration for the workplace help-seeking scenario.
 *
 * Contains OCEAN trait profiles for each action and the mapping
 * of persons to their available actions. This keeps scenario-specific
 * data out of the generic Temper class.
 */
public class HelpScenarioConfig {

    /** OCEAN trait profiles for each action in the help scenario.
     *  Must match the plan annotations in workplace_cfr_learning.asl exactly. */
    private static final Map<String, Map<String, Double>> ACTION_TRAITS = new HashMap<>();

    static {
        // Bob actions (senior, moderate reciprocity)
        ACTION_TRAITS.put("help_bob", Map.of(
            "agreeableness", 0.8, "conscientiousness", 0.7,
            "extraversion", 0.5, "openness", 0.4, "neuroticism", 0.3));
        ACTION_TRAITS.put("decline_bob", Map.of(
            "conscientiousness", 0.8, "agreeableness", 0.2,
            "extraversion", 0.2, "openness", 0.2, "neuroticism", 0.1));
        ACTION_TRAITS.put("delay_bob", Map.of(
            "openness", 0.7, "conscientiousness", 0.7,
            "agreeableness", 0.4, "extraversion", 0.3, "neuroticism", 0.1));

        // Carol actions (exploitative junior)
        ACTION_TRAITS.put("help_carol", Map.of(
            "agreeableness", 0.9, "neuroticism", 0.8,
            "conscientiousness", 0.2, "extraversion", 0.5, "openness", 0.3));
        ACTION_TRAITS.put("decline_carol", Map.of(
            "conscientiousness", 0.9, "agreeableness", 0.1,
            "extraversion", 0.1, "openness", 0.3, "neuroticism", 0.05));
        ACTION_TRAITS.put("teach_carol", Map.of(
            "openness", 0.8, "conscientiousness", 0.6,
            "agreeableness", 0.4, "extraversion", 0.4, "neuroticism", 0.2));

        // Dave actions (reciprocal PM)
        ACTION_TRAITS.put("help_dave", Map.of(
            "openness", 0.7, "extraversion", 0.6,
            "conscientiousness", 0.5, "agreeableness", 0.5, "neuroticism", 0.1));
        ACTION_TRAITS.put("decline_dave", Map.of(
            "conscientiousness", 0.6, "agreeableness", 0.2,
            "extraversion", 0.1, "openness", 0.2, "neuroticism", 0.1));
        ACTION_TRAITS.put("suggest_dave", Map.of(
            "openness", 0.7, "conscientiousness", 0.7,
            "agreeableness", 0.4, "extraversion", 0.3, "neuroticism", 0.1));
    }

    /** Get the OCEAN trait profile for a given action. */
    public static Map<String, Double> getActionTraits(String action) {
        return ACTION_TRAITS.get(action);
    }

    /** Get all action trait profiles. */
    public static Map<String, Map<String, Double>> getAllActionTraits() {
        return ACTION_TRAITS;
    }

    /** Get possible actions for a person. */
    public static String[] getActionsForPerson(String person) {
        switch (person.toLowerCase()) {
            case "bob":   return new String[]{"help_bob", "decline_bob", "delay_bob"};
            case "carol": return new String[]{"help_carol", "decline_carol", "teach_carol"};
            case "dave":  return new String[]{"help_dave", "decline_dave", "suggest_dave"};
            default:      return new String[]{};
        }
    }

    /** Initialize behavioral memory with the scenario's characters. */
    public static void initBehavioralMemory(BehavioralMemory memory) {
        // Bob: senior, moderate reciprocity (sometimes helps back)
        memory.addPerson("bob", "Bob", 0.6, 0.4);
        // Carol: junior, exploitative (rarely helps back)
        memory.addPerson("carol", "Carol", 0.2, 0.1);
        // Dave: PM, highly reciprocal (almost always helps back)
        memory.addPerson("dave", "Dave", 0.8, 0.9);

        System.out.println("[BEHAVIOR MEMORY] Initialized: Bob(0.6/0.4), Carol(0.2/0.1), Dave(0.8/0.9)");
    }
}
