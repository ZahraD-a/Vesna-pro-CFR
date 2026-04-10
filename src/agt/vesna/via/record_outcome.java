package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.Temper;
import vesna.VesnaAgent;

import java.util.HashMap;
import java.util.Map;
import java.util.Iterator;

import static jason.asSyntax.ASSyntax.*;

/**
 * Internal action: vesna.via.record_outcome(Event, Reward, Action, Person)
 *
 * Records outcome for CFR-inspired regret matching personality learning.
 * Base rewards are uniform; behavioral memory creates divergence over time.
 *
 * Usage in ASL:
 *   vesna.via.record_outcome(success, 0.5, help_bob, bob).
 *   vesna.via.record_outcome(failure, -0.3, help_carol, carol).
 *   vesna.via.record_outcome(neutral, 0.0, decline_dave, dave).
 */
public class record_outcome extends DefaultInternalAction {

    /** Reciprocity shaping coefficient (alpha in Eq. reward_shaping of the paper).
     *  Can be overridden via -Dalpha=0.4 on the JVM command line for sensitivity checks. */
    private static final double ALPHA = Double.parseDouble(
        System.getProperty("alpha", "0.6"));
    private static final double BETA  = Double.parseDouble(
        System.getProperty("beta", "0.3"));
    private static final double GAMMA = Double.parseDouble(
        System.getProperty("gamma", "0.2"));

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();

        if (args.length < 4) {
            ts.getLogger().warning("[record_outcome] Usage: record_outcome(Event, Reward, Action, Person)");
            return false;
        }

        // Parse arguments
        String event = args[0].toString().toLowerCase().trim();
        double baseReward = ((NumberTerm) args[1]).solve();
        String action = args[2].toString();
        String person = args[3].toString().toLowerCase();

        // ========== BEHAVIORAL MEMORY UPDATE ==========
        boolean helped = action.contains("help") || action.contains("join");
        temper.updateBehavioralMemory(person, helped);

        // ========== REWARD ENHANCEMENT FROM BEHAVIORAL MEMORY ==========
        // Base rewards are uniform (+0.5 success, -0.3 failure, 0.0 neutral).
        // Behavioral memory creates divergence: the agent LEARNS who to trust.
        double enhancedReward = baseReward;

        double reciprocity = temper.getBehavioralValue(person, "reciprocity");
        double relationship = temper.getBehavioralValue(person, "relationship");
        double isExploitative = temper.getBehavioralValue(person, "is_exploitative");

        if (helped) {
            // Reciprocity shaping (Hughes et al. 2018, Zhou et al. 2024):
            // bonus for helping reciprocal people, penalty for exploiters.
            enhancedReward += (reciprocity - 0.5) * ALPHA;
        }

        if (action.contains("decline") && isExploitative > 0.5) {
            // Defection/boycott bonus (Ren & Zeng 2024):
            // reward for declining detected exploiters.
            enhancedReward += BETA;
        }

        // Potential-based shaping (Ng et al. 1999):
        // relationship score acts as a potential function.
        enhancedReward += (relationship - 0.5) * GAMMA;

        ts.getLogger().info(String.format(
            "[CFR] %s %s: base=%.2f -> enhanced=%.3f (recip=%.2f, rel=%.2f, exploit=%s)",
            person, action, baseReward, enhancedReward, reciprocity, relationship,
            isExploitative > 0.5 ? "YES" : "no"));

        // ========== RECORD TO TEMPER FOR CFR ==========
        temper.recordHelpOutcome(action, enhancedReward, person);

        return true;
    }
}
