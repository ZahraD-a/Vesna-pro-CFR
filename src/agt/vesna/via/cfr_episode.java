package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.Temper;
import vesna.VesnaAgent;
import vesna.personality.PolicyLogger;

import java.io.*;
import java.nio.file.*;
import java.util.HashMap;
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

    /** 1-indexed episode currently in progress (incremented at episode end). */
    public static int getCurrentEpisode() { return episodeCounter + 1; }
    private static final String ADAPT_LOG = "adapted_reciprocity.csv";
    private static boolean adaptHeaderWritten = false;

    private static void logAdaptedReciprocity(int episode,
            vesna.BehavioralMemory.PersonMemory carol,
            vesna.BehavioralMemory.PersonMemory bob,
            vesna.BehavioralMemory.PersonMemory dave) {
        try (PrintWriter pw = new PrintWriter(new FileWriter(ADAPT_LOG, true))) {
            if (!adaptHeaderWritten) {
                pw.println("episode,carol_adapted,carol_innate,bob_adapted,bob_innate,dave_adapted,dave_innate,carol_observed_ratio,carol_phi");
                adaptHeaderWritten = true;
            }
            double ca  = carol != null ? carol.adaptedReciprocity : 0;
            double ci  = carol != null ? carol.reciprocity        : 0;
            double ba  = bob   != null ? bob.adaptedReciprocity   : 0;
            double bi  = bob   != null ? bob.reciprocity          : 0;
            double da  = dave  != null ? dave.adaptedReciprocity  : 0;
            double di  = dave  != null ? dave.reciprocity         : 0;
            double cor = carol != null ? carol.reciprocityRatio   : 0;
            int    phi = (carol != null && carol.isExploitative)  ? 1 : 0;
            pw.printf("%d,%.4f,%.2f,%.4f,%.2f,%.4f,%.2f,%.4f,%d%n",
                      episode, ca, ci, ba, bi, da, di, cor, phi);
        } catch (IOException e) {
            System.err.println("[ADAPT LOG] " + e.getMessage());
        }
    }

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

            // Capture last actions BEFORE startNewEpisode clears them
            String lastCarolAction = temper.getLastActionForPerson("carol");
            String lastBobAction   = temper.getLastActionForPerson("bob");
            String lastDaveAction  = temper.getLastActionForPerson("dave");

            // Capture end-of-episode mood BEFORE startNewEpisode resets it
            Map<String, Double> endOfEpisodeMood = new HashMap<>(temper.getMood());

            // CFR learning: updates personality from regrets, then resets mood
            temper.startNewEpisode();

            // ── COLLEAGUE ADAPTATION ──────────────────────────────────────
            // Each colleague observes what Alice did and adapts reciprocity.
            vesna.BehavioralMemory.PersonMemory carolMem =
                temper.getBehavioralMemoryPerson("carol");
            vesna.BehavioralMemory.PersonMemory bobMem =
                temper.getBehavioralMemoryPerson("bob");
            vesna.BehavioralMemory.PersonMemory daveMem =
                temper.getBehavioralMemoryPerson("dave");

            if (carolMem != null) carolMem.adaptReciprocity(lastCarolAction.contains("decline"));
            if (bobMem   != null) bobMem.adaptReciprocity(lastBobAction.contains("decline"));
            if (daveMem  != null) daveMem.adaptReciprocity(lastDaveAction.contains("decline"));
            
            // Carol's personality update (CFR-based learning)
            if (carolMem != null && carolMem.learnsViaCFR) {
                carolMem.updatePersonalityFromRegret();
            }
            // ─────────────────────────────────────────────────────────────

            // Log adapted reciprocity to CSV for verification
            logAdaptedReciprocity(episodeCounter, carolMem, bobMem, daveMem);

            // Log personality (post-update) and mood (end-of-episode) to CSV
            PolicyLogger.logEpisode(episodeCounter, temper.getPersonality(),
                                    endOfEpisodeMood, totalReward);

            // Log cumulative regrets to CSV
            PolicyLogger.logRegrets(episodeCounter, temper.getHelpCumulativeRegrets());
            
            // Log Carol's personality and regrets if she's learning
            if (carolMem != null && carolMem.learnsViaCFR) {
                PolicyLogger.logCarolPersonality(episodeCounter, carolMem.personality);
                PolicyLogger.logCarolRegrets(episodeCounter, carolMem.cumulativeRegret);
            }
        }

        System.out.println("======================================\n");
        System.out.flush();

        return true;
    }
}
