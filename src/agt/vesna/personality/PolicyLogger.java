package vesna.personality;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

/**
 * Logs personality evolution and CFR regrets to CSV files.
 *
 * Personality CSV: timestamp, episode, O, C, E, A, N, total_reward
 * Regret CSV:      timestamp, episode, [9 action regrets]
 */
public class PolicyLogger {

    private static final String POLICY_LOG_FILE = "personality_evolution.csv";
    private static final String REGRET_LOG_FILE = "cfr_regrets.csv";
    private static final DateTimeFormatter TIME_FORMAT =
        DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS");

    /** OCEAN trait names in canonical order */
    private static final String[] OCEAN_TRAITS = {
        "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"
    };

    /** Mood trait names in canonical order */
    private static final String[] MOOD_TRAITS = {
        "stress", "satisfaction", "social_energy"
    };

    /** All help scenario actions in canonical order */
    /**
     * Alice's plan names per colleague, in CSV column order.
     * Carol's slots use "help_alice / decline_alice / teach_alice" because
     * Carol is the CFR partner: her requests elicit those plan names from
     * Alice, and the corresponding infoset is keyed on those names.
     */
    private static final String[] HELP_ACTIONS = {
        "help_bob",    "decline_bob",    "delay_bob",
        "help_alice",  "decline_alice",  "teach_alice",
        "help_dave",   "decline_dave",   "suggest_dave"
    };

    /**
     * Log personality and mood state at end of episode.
     */
    public static void logEpisode(int episode,
                                   Map<String, Double> personality,
                                   Map<String, Double> mood,
                                   double totalReward) {
        try {
            if (!Files.exists(Paths.get(POLICY_LOG_FILE))) {
                writeHeader();
            }

            StringBuilder row = new StringBuilder();
            row.append(LocalDateTime.now().format(TIME_FORMAT)).append(",");
            row.append(episode).append(",");
            for (String trait : OCEAN_TRAITS) {
                row.append(personality.getOrDefault(trait, 0.0)).append(",");
            }
            for (String m : MOOD_TRAITS) {
                row.append(String.format("%.4f", mood.getOrDefault(m, 0.0))).append(",");
            }
            row.append(String.format("%.3f", totalReward));

            Files.write(Paths.get(POLICY_LOG_FILE),
                (row.toString() + System.lineSeparator()).getBytes(),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);

        } catch (IOException e) {
            System.err.println("[POLICY] Failed to log episode: " + e.getMessage());
        }
    }

    private static void writeHeader() throws IOException {
        StringBuilder header = new StringBuilder("timestamp,episode,");
        for (String trait : OCEAN_TRAITS) {
            header.append(trait).append(",");
        }
        for (String m : MOOD_TRAITS) {
            header.append(m).append(",");
        }
        header.append("total_reward");

        Files.write(Paths.get(POLICY_LOG_FILE),
            (header.toString() + System.lineSeparator()).getBytes(),
            StandardOpenOption.CREATE);
    }

    /**
     * Log initial personality and mood (episode 0, before learning).
     */
    public static void logInitial(Map<String, Double> personality, Map<String, Double> mood) {
        logEpisode(0, personality, mood, 0.0);
    }

    /**
     * Log CFR cumulative regrets.
     */
    public static void logRegrets(int episode, Map<String, Double> regrets) {
        try {
            if (!Files.exists(Paths.get(REGRET_LOG_FILE))) {
                writeRegretHeader();
            }

            StringBuilder row = new StringBuilder();
            row.append(LocalDateTime.now().format(TIME_FORMAT)).append(",");
            row.append(episode);
            for (String action : HELP_ACTIONS) {
                row.append(",").append(regrets.getOrDefault(action, 0.0));
            }

            Files.write(Paths.get(REGRET_LOG_FILE),
                (row.toString() + System.lineSeparator()).getBytes(),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);

        } catch (IOException e) {
            System.err.println("[POLICY] Failed to log regrets: " + e.getMessage());
        }
    }

    private static void writeRegretHeader() throws IOException {
        StringBuilder header = new StringBuilder("timestamp,episode");
        for (String action : HELP_ACTIONS) {
            header.append(",").append(action);
        }

        Files.write(Paths.get(REGRET_LOG_FILE),
            (header.toString() + System.lineSeparator()).getBytes(),
            StandardOpenOption.CREATE);
    }

    public static void reset() {
        try {
            Files.deleteIfExists(Paths.get(POLICY_LOG_FILE));
            Files.deleteIfExists(Paths.get(REGRET_LOG_FILE));
            Files.deleteIfExists(Paths.get("carol_personality_evolution.csv"));
            Files.deleteIfExists(Paths.get("carol_cfr_regrets.csv"));
        } catch (IOException e) {
            System.err.println("[POLICY] Failed to reset: " + e.getMessage());
        }
    }
    
    /**
     * Log Carol's personality evolution (if she learns via CFR).
     */
    public static void logCarolPersonality(int episode, Map<String, Double> carolPersonality) {
        try {
            String filepath = "carol_personality_evolution.csv";
            if (!Files.exists(Paths.get(filepath))) {
                writeCarolHeader();
            }

            StringBuilder row = new StringBuilder();
            row.append(LocalDateTime.now().format(TIME_FORMAT)).append(",");
            row.append(episode).append(",");
            for (String trait : OCEAN_TRAITS) {
                row.append(String.format("%.4f", carolPersonality.getOrDefault(trait, 0.0))).append(",");
            }
            // Remove trailing comma
            String rowStr = row.toString();
            if (rowStr.endsWith(",")) {
                rowStr = rowStr.substring(0, rowStr.length() - 1);
            }

            Files.write(Paths.get(filepath),
                (rowStr + System.lineSeparator()).getBytes(),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);

        } catch (IOException e) {
            System.err.println("[CAROL POLICY] Failed to log personality: " + e.getMessage());
        }
    }

    private static void writeCarolHeader() throws IOException {
        StringBuilder header = new StringBuilder("timestamp,episode");
        for (String trait : OCEAN_TRAITS) {
            header.append(",").append("carol_").append(trait);
        }

        Files.write(Paths.get("carol_personality_evolution.csv"),
            (header.toString() + System.lineSeparator()).getBytes(),
            StandardOpenOption.CREATE);
    }
    
    /**
     * Log Carol's CFR regrets for each action.
     */
    public static void logCarolRegrets(int episode, Map<String, Double> carolRegrets) {
        try {
            String filepath = "carol_cfr_regrets.csv";
            if (!Files.exists(Paths.get(filepath))) {
                writeCarolRegretHeader();
            }

            StringBuilder row = new StringBuilder();
            row.append(LocalDateTime.now().format(TIME_FORMAT)).append(",");
            row.append(episode).append(",");
            String[] carolActions = {"help", "decline", "reciprocate"};
            for (String action : carolActions) {
                row.append(String.format("%.4f", carolRegrets.getOrDefault(action, 0.0))).append(",");
            }
            // Remove trailing comma
            String rowStr = row.toString();
            if (rowStr.endsWith(",")) {
                rowStr = rowStr.substring(0, rowStr.length() - 1);
            }

            Files.write(Paths.get(filepath),
                (rowStr + System.lineSeparator()).getBytes(),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);

        } catch (IOException e) {
            System.err.println("[CAROL POLICY] Failed to log regrets: " + e.getMessage());
        }
    }

    private static void writeCarolRegretHeader() throws IOException {
        StringBuilder header = new StringBuilder("timestamp,episode,carol_help_regret,carol_decline_regret,carol_reciprocate_regret");

        Files.write(Paths.get("carol_cfr_regrets.csv"),
            (header.toString() + System.lineSeparator()).getBytes(),
            StandardOpenOption.CREATE);
    }

    public static String getLogFilePath() { return POLICY_LOG_FILE; }
    public static String getRegretLogFilePath() { return REGRET_LOG_FILE; }
}
