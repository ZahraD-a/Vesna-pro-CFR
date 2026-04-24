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
 * <p>Carol's internal action space is <code>{help, decline, reciprocate}</code>.
 * Alice's observed action is mapped as follows:</p>
 * <ul>
 *   <li><code>help_alice</code>    &rarr; <code>reciprocate</code>
 *       (Alice helps her, so she reciprocates in turn)</li>
 *   <li><code>decline_alice</code> &rarr; <code>decline</code>
 *       (Alice declines, so Carol learns boundary-setting pays)</li>
 *   <li><code>teach_alice</code>   &rarr; <code>help</code>
 *       (Alice mentors, so Carol learns helping pays)</li>
 * </ul>
 *
 * <p>The reward is added to Carol's cumulative regret for the mapped action
 * in her {@link BehavioralMemory.PersonMemory}; this is the regret stream
 * that {@link BehavioralMemory.PersonMemory#updatePersonalityFromRegret()}
 * reads at episode end. The same reward is also forwarded to Temper's
 * diagnostic regret table for logging purposes.</p>
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
        if (aliceAction.contains("help_alice")) {
            carolAction = "reciprocate";
        } else if (aliceAction.contains("decline_alice")) {
            carolAction = "decline";
        } else if (aliceAction.contains("teach_alice")) {
            carolAction = "help";
        } else {
            carolAction = aliceAction;
        }

        BehavioralMemory.PersonMemory carolMem = temper.getBehavioralMemoryPerson("carol");
        if (carolMem != null && carolMem.learnsViaCFR) {
            carolMem.recordDecisionOutcome(carolAction, reward);
        }

        // Secondary diagnostic channel: keep Temper's carolInformationSets in sync.
        temper.recordCarolOutcome(aliceAction, reward);

        ts.getLogger().info(String.format(
            "[Carol CFR] alice=%s -> carol=%s reward=%+.3f",
            aliceAction, carolAction, reward));
        return true;
    }
}
