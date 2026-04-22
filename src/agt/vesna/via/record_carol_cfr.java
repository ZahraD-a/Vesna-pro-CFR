package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.Temper;
import vesna.VesnaAgent;

/**
 * Internal action: vesna.via.record_carol_cfr(Action, Reward)
 *
 * Records Carol's decision outcome for CFR-inspired personality learning.
 * Called from Carol's response evaluation in workplace_cfr_learning.asl
 * when Carol chooses help/decline/reciprocate based on CFR decisions.
 *
 * Usage in ASL:
 *   vesna.via.record_carol_cfr(help, 0.8).
 *   vesna.via.record_carol_cfr(decline, -0.4).
 *   vesna.via.record_carol_cfr(reciprocate, 0.5).
 */
public class record_carol_cfr extends DefaultInternalAction {

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();

        if (args.length < 2) {
            ts.getLogger().warning("[record_carol_cfr] Usage: record_carol_cfr(Action, Reward)");
            return false;
        }

        String action = args[0].toString();
        double reward = ((NumberTerm) args[1]).solve();

        ts.getLogger().info(String.format(
            "[Carol CFR Outcome] Action: %s, Reward: %.3f", action, reward));

        // Record Carol's outcome via Temper's CFR system
        // This will update Carol's personality based on regret matching
        temper.recordCarolOutcome(action, reward);

        return true;
    }
}
