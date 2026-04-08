package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.VesnaAgent;
import vesna.Temper;

/**
 * Internal action: vesna.via.set_decision_context(Person)
 *
 * Sets the current decision context (information set) for CFR tracking.
 * Must be called before each person's plan selection so that
 * decision traces are recorded under the correct info set.
 *
 * Usage in ASL:
 *   vesna.via.set_decision_context(bob).
 */
public class set_decision_context extends DefaultInternalAction {

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {
        if (args.length < 1) return false;

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();
        if (temper == null) return false;

        String person = args[0].toString().toLowerCase();
        String infosetName = "help_" + person;
        temper.setCurrentStage(infosetName);

        return true;
    }
}
