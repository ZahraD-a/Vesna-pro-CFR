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
            // Reciprocity bonus/penalty: emerges from observed behavior
            // Helping reciprocal people → bonus; helping exploiters → penalty
            enhancedReward += (reciprocity - 0.5) * 0.6;
        }

        if (action.contains("decline") && isExploitative > 0.5) {
            // Boundary-setting bonus: reward for declining known exploiters
            enhancedReward += 0.3;
        }

        // Relationship bonus: better relationships yield better outcomes
        enhancedReward += (relationship - 0.5) * 0.2;

        ts.getLogger().info(String.format(
            "[CFR] %s %s: base=%.2f -> enhanced=%.3f (recip=%.2f, rel=%.2f, exploit=%s)",
            person, action, baseReward, enhancedReward, reciprocity, relationship,
            isExploitative > 0.5 ? "YES" : "no"));

        // ========== RECORD TO TEMPER FOR CFR ==========
        temper.recordHelpOutcome(action, enhancedReward, person);

        return true;
    }
}
