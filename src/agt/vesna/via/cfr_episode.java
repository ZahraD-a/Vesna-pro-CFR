package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.Temper;
import vesna.VesnaAgent;
import vesna.RewardMachine;
import vesna.personality.PolicyLogger;

import java.util.Map;

/**
 * Internal action: vesna.cfr_episode
 *
 * Signals the END of an episode (task/training cycle).
 * Does four things:
 *   1. Triggers CFR learning to update personality
 *   2. Logs personality evolution to CSV
 *   3. Persists personality to file for next run
 *   4. Resets reward tracking for next episode
 *
 * <p><b>USAGE IN ASL:</b></p>
 * <pre>
 *   // At the end of each episode
 *   vesna.cfr_episode.
 * </pre>
 *
 * @author VesnaPro CFR Extension
 */
public class cfr_episode extends DefaultInternalAction {

    /** Episode counter for logging */
    private static int episodeCounter = 0;

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        Temper temper = agent.getTemper();
        RewardMachine rm = agent.getRewardMachine();

        episodeCounter++;

        // Flush any pending output first
        System.out.flush();
        System.err.flush();

        // ========== STEP 1: Trigger CFR Learning ==========
        double totalReward = 0.0;
        if (temper != null) {
            System.out.println("\n========== EPISODE " + episodeCounter + " COMPLETE ==========");

            // Print personality BEFORE update
            Map<String, Double> personalityBefore = temper.getPersonality();
            System.out.println("Personality BEFORE: " + formatPersonality(personalityBefore));

            // Get total reward before CFR update
            totalReward = temper.getTotalEpisodeReward();

            temper.startNewEpisode();

            // Print personality AFTER update
            Map<String, Double> personalityAfter = temper.getPersonality();
            System.out.println("Personality AFTER:  " + formatPersonality(personalityAfter));
        } else {
            ts.getLogger().warning("[CFR] No Temper configured for learning");
        }

        // ========== STEP 2: Log Personality Evolution ==========
        if (temper != null) {
            PolicyLogger.logEpisode(episodeCounter, temper.getPersonality(), totalReward);
            PolicyLogger.printSummary(episodeCounter, temper.getPersonality(), totalReward);

            // Also log regrets for visualization
            PolicyLogger.logRegrets(episodeCounter, temper.getCoffeeCumulativeRegrets());
        }

        // ========== STEP 3: Print Reward Summary ==========
        if (rm != null) {
            rm.printSummary();
            rm.reset();
        }

        System.out.println("======================================\n");
        System.out.flush();

        return true;
    }

    /**
     * Format personality map as string.
     */
    private String formatPersonality(Map<String, Double> personality) {
        StringBuilder sb = new StringBuilder();
        sb.append("{");
        boolean first = true;
        for (Map.Entry<String, Double> entry : personality.entrySet()) {
            if (!first) sb.append(", ");
            sb.append(entry.getKey()).append("=").append(String.format("%.3f", entry.getValue()));
            first = false;
        }
        sb.append("}");
        return sb.toString();
    }
}
