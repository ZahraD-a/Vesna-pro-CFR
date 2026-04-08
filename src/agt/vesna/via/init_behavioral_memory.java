package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.VesnaAgent;
import vesna.Temper;

/**
 * Internal action: vesna.via.init_behavioral_memory
 *
 * Initializes behavioral memory for tracking relationships with
 * Bob, Carol, and Dave in the help-seeking scenario.
 *
 * Usage in ASL:
 *   vesna.via.init_behavioral_memory.
 */
public class init_behavioral_memory extends DefaultInternalAction {

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {
        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();

        if (temper != null) {
            temper.initBehavioralMemory();
            return true;
        }

        ts.getLogger().warning("[init_behavioral_memory] Temper not found");
        return false;
    }
}
