package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.Temper;
import vesna.VesnaAgent;

/**
 * Internal action: vesna.via.print_cfr_stats
 *
 * Prints detailed CFR statistics including:
 *   - Information sets visited
 *   - Cumulative regrets at each infoset
 *   - Average strategies
 *   - Personality evolution
 *
 * Usage in ASL:
 *   vesna.via.print_cfr_stats.
 *
 * @author VesnaPro CFR Extension
 */
public class print_cfr_stats extends DefaultInternalAction {

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();

        if (temper == null) {
            ts.getLogger().warning("[CFR] No Temper configured");
            return true;
        }

        temper.printCFRStats();

        return true;
    }
}
