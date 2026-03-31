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
 * Prints the current personality profile and logs initial state.
 *
 * Usage in ASL:
 *   vesna.via.print_personality.
 *
 * @author VesnaPro CFR Extension
 */
public class print_personality extends DefaultInternalAction {

    /** Track if initial state has been logged */
    private static boolean initialLogged = false;

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();

        if (temper == null) {
            System.out.println("\n========== PERSONALITY ==========");
            System.out.println("No Temper configured.");
            System.out.println("======================================\n");
            return true;
        }

        Map<String, Double> personality = temper.getPersonality();

        System.out.println("\n========== PERSONALITY PROFILE ==========");

        double cautious = personality.getOrDefault("cautious", 0.5);
        double bold = personality.getOrDefault("bold", 0.5);
        double curious = personality.getOrDefault("curious", 0.5);

        System.out.printf("  Cautious:  %.3f", cautious);
        if (cautious > 0.7) System.out.print(" (Very Careful)");
        else if (cautious < 0.3) System.out.print(" (Not Careful)");
        else System.out.print(" (Balanced)");
        System.out.println();

        System.out.printf("  Bold:      %.3f", bold);
        if (bold > 0.7) System.out.print(" (Very Bold)");
        else if (bold < 0.3) System.out.print(" (Not Bold)");
        else System.out.print(" (Balanced)");
        System.out.println();

        System.out.printf("  Curious:   %.3f", curious);
        if (curious > 0.7) System.out.print(" (Very Curious)");
        else if (curious < 0.3) System.out.print(" (Not Curious)");
        else System.out.print(" (Balanced)");
        System.out.println();

        System.out.println("\n  Preferred Strategy:");
        if (cautious > bold + 0.2) {
            System.out.println("    → Likely to choose safe/reliable options");
        } else if (bold > cautious + 0.2) {
            System.out.println("    → Likely to choose risky/exploratory options");
        } else {
            System.out.println("    → Balanced between safe and risky options");
        }

        System.out.println("=============================================\n");

        // Log initial state (episode 0) on first call
        if (!initialLogged) {
            PolicyLogger.logInitial(personality);
            initialLogged = true;
        }

        return true;
    }
}
