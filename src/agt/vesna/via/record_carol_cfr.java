package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.BehavioralMemory;
import vesna.Temper;
import vesna.VesnaAgent;

/**
 * Internal action: <code>vesna.via.record_carol_cfr(AliceAction, Reward)</code>
 *
 * <p>Records the outcome of a Carol-facing interaction into Carol's CFR
 * state, driving Carol's own personality update at the next learning
 * boundary.</p>
 *
 * <p>Carol's internal action space is <code>{carol_help_alice, carol_decline_alice, carol_reciprocate_alice}</code>.
 * Alice's observed action is mapped as follows:</p>
 * <ul>
 *   <li><code>alice_help_carol</code>    &rarr; <code>carol_reciprocate_alice</code>
 *       (Alice helps her, so she reciprocates in turn)</li>
 *   <li><code>alice_decline_carol</code> &rarr; <code>carol_decline_alice</code>
 *       (Alice declines, so Carol learns boundary-setting pays)</li>
 *   <li><code>alice_teach_carol</code>   &rarr; <code>carol_help_alice</code>
 *       (Alice mentors, so Carol learns helping pays)</li>
 * </ul>
 *
 * <p>The reward is added to Carol's cumulative regret for the mapped action
 * in her {@link BehavioralMemory.PersonMemory}; this is the regret stream
 * that {@link BehavioralMemory.PersonMemory#updatePersonalityFromRegret()}
 * reads at episode end.</p>
 *
 * <h3>Carol = observational CFR (asymmetric with Alice)</h3>
 * <p>Alice runs <i>self-CFR</i>: her regret is computed against her own plans'
 * historical mean payoffs (see {@link Temper#updatePersonalityFromCFR}).
 * Carol runs <i>observational CFR</i>: her regret is over the action she
 * attributes to Alice's behaviour, with an instantaneous-counterfactual
 * recipe inside {@link BehavioralMemory.PersonMemory#recordDecisionOutcome}.
 * This asymmetry is intentional — Carol's role is to <i>react to Alice</i>,
 * not to optimise her own utility independently. It is what produces the
 * social-trust-reversal dynamic reported in the paper (φ(Carol) deactivation
 * once Alice's perceived help-rate drops past threshold).</p>
 */
public class record_carol_cfr extends DefaultInternalAction {

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {

        if (args.length < 2) {
            ts.getLogger().warning("[record_carol_cfr] Usage: record_carol_cfr(AliceAction, Reward)");
            return false;
        }

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();

        String aliceAction = args[0].toString();
        double reward = ((NumberTerm) args[1]).solve();

        String carolAction;
        if (aliceAction.contains("alice_help_carol")) {
            carolAction = "carol_reciprocate_alice";
        } else if (aliceAction.contains("alice_decline_carol")) {
            carolAction = "carol_decline_alice";
        } else if (aliceAction.contains("alice_teach_carol")) {
            carolAction = "carol_help_alice";
        } else {
            carolAction = aliceAction;
        }

        // Single source of truth for Carol's CFR state: BehavioralMemory.PersonMemory.
        // (The previous Temper-side mirror was unwired and has been removed.)
        BehavioralMemory.PersonMemory carolMem = temper.getBehavioralMemoryPerson("carol");
        if (carolMem != null && carolMem.learnsViaCFR) {
            carolMem.recordDecisionOutcome(carolAction, reward);
        }

        ts.getLogger().info(String.format(
            "[Carol CFR] alice=%s -> carol=%s reward=%+.3f",
            aliceAction, carolAction, reward));
        return true;
    }
}
