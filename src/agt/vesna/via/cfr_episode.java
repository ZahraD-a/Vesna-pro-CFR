package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.Temper;
import vesna.VesnaAgent;
import vesna.personality.PolicyLogger;

import java.util.Map;

/**
 * Internal action: vesna.via.cfr_episode
 *
 * Signals end of an episode. Triggers:
 *   1. CFR personality update (regret matching)
 *   2. Personality evolution logging to CSV
 *   3. Regret logging to CSV
 *
 * Usage in ASL:
 *   vesna.via.cfr_episode.
 */
public class cfr_episode extends DefaultInternalAction {

    private static int episodeCounter = 0;

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();

        episodeCounter++;
        System.out.flush();

        double totalReward = 0.0;
        if (temper != null) {
            System.out.println("\n========== EPISODE " + episodeCounter + " COMPLETE ==========");
            totalReward = temper.getTotalEpisodeReward();

            // CFR learning: updates personality from regrets
            temper.startNewEpisode();

            // Log personality evolution to CSV
            PolicyLogger.logEpisode(episodeCounter, temper.getPersonality(), totalReward);

            // Log cumulative regrets to CSV
            PolicyLogger.logRegrets(episodeCounter, temper.getHelpCumulativeRegrets());
        }

        System.out.println("======================================\n");
        System.out.flush();

        return true;
    }
}
