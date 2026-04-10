package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.VesnaAgent;
import vesna.Temper;
import vesna.personality.PolicyLogger;

import java.util.Map;

/**
 * Internal action: vesna.via.print_personality
 *
 * Prints the current OCEAN personality profile with interpretations.
 *
 * Usage in ASL:
 *   vesna.via.print_personality.
 */
public class print_personality extends DefaultInternalAction {

    private static boolean initialLogged = false;

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();

        if (temper == null) {
            System.out.println("[PERSONALITY] No Temper configured.");
            return true;
        }

        Map<String, Double> personality = temper.getPersonality();

        double O = personality.getOrDefault("openness", 0.5);
        double C = personality.getOrDefault("conscientiousness", 0.5);
        double E = personality.getOrDefault("extraversion", 0.5);
        double A = personality.getOrDefault("agreeableness", 0.5);
        double N = personality.getOrDefault("neuroticism", 0.5);

        System.out.println("\n========== PERSONALITY PROFILE (OCEAN) ==========");
        System.out.printf("  Openness:          %.3f %s%n", O, label(O, "Creative", "Traditional"));
        System.out.printf("  Conscientiousness: %.3f %s%n", C, label(C, "Disciplined", "Spontaneous"));
        System.out.printf("  Extraversion:      %.3f %s%n", E, label(E, "Social", "Reserved"));
        System.out.printf("  Agreeableness:     %.3f %s%n", A, label(A, "Helpful", "Competitive"));
        System.out.printf("  Neuroticism:       %.3f %s%n", N, label(N, "Sensitive", "Stable"));

        System.out.println("\n  Behavioral Tendencies:");
        if (A > 0.7) System.out.println("    -> Likely to help everyone (risk of exploitation)");
        else if (A < 0.3) System.out.println("    -> Likely to set boundaries, decline requests");
        else System.out.println("    -> Selective helper (context-dependent)");

        if (C > 0.7) System.out.println("    -> Focuses on own work, very reliable");
        if (E > 0.7) System.out.println("    -> Seeks social interactions, high visibility");
        else if (E < 0.3) System.out.println("    -> Avoids time-consuming social obligations");

        System.out.println("=================================================\n");

        // Log initial state on first call
        if (!initialLogged) {
            PolicyLogger.logInitial(personality, temper.getMood());
            initialLogged = true;
        }

        return true;
    }

    private String label(double val, String high, String low) {
        if (val > 0.7) return "(Very " + high + ")";
        if (val < 0.3) return "(Very " + low + ")";
        return "(Balanced)";
    }
}
