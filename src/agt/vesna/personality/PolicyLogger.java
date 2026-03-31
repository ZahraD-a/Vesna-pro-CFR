package vesna.personality;

import vesna.Temper;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

/**
 * Policy Logger for tracking personality evolution over time.
 *
 * Logs personality changes to CSV file with timestamp, episode, and trait values.
 * Format: timestamp,episode,cautious,bold,curious,total_reward
 *
 * @author VesnaPro CFR Extension - Coffee Decision Scenario
 */
public class PolicyLogger {

    private static final String POLICY_LOG_FILE = "personality_evolution.csv";
    private static final String REGRET_LOG_FILE = "cfr_regrets.csv";
    private static final DateTimeFormatter TIME_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS");
    private static boolean headerWritten = false;
    private static boolean regretHeaderWritten = false;

    /**
     * Log personality state at the end of an episode.
     *
     * @param episodeNumber Current episode number
     * @param personality Current personality values
     * @param totalReward Total reward for this episode
     */
    public static void logEpisode(int episodeNumber, Map<String, Double> personality, double totalReward) {
        try {
            // Create header if file doesn't exist
            if (!Files.exists(Paths.get(POLICY_LOG_FILE))) {
                writeHeader();
            }

            String timestamp = LocalDateTime.now().format(TIME_FORMAT);

            StringBuilder row = new StringBuilder();
            row.append(timestamp).append(",");
            row.append(episodeNumber).append(",");
            row.append(personality.getOrDefault("cautious", 0.5)).append(",");
            row.append(personality.getOrDefault("bold", 0.5)).append(",");
            row.append(personality.getOrDefault("curious", 0.5)).append(",");
            row.append(String.format("%.3f", totalReward));

            // Append to file
            Files.write(Paths.get(POLICY_LOG_FILE),
                (row.toString() + System.lineSeparator()).getBytes(),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);

            System.out.println("[POLICY] Logged episode " + episodeNumber + " to " + POLICY_LOG_FILE);

        } catch (IOException e) {
            System.err.println("[POLICY] Failed to log episode: " + e.getMessage());
        }
    }

    /**
     * Write CSV header.
     */
    private static void writeHeader() throws IOException {
        String header = "timestamp,episode,cautious,bold,curious,total_reward";
        Files.write(Paths.get(POLICY_LOG_FILE),
            (header + System.lineSeparator()).getBytes(),
            StandardOpenOption.CREATE);
        headerWritten = true;
        System.out.println("[POLICY] Created log file: " + POLICY_LOG_FILE);
    }

    /**
     * Log the initial personality (episode 0, before any learning).
     */
    public static void logInitial(Map<String, Double> personality) {
        logEpisode(0, personality, 0.0);
    }

    /**
     * Get the log file path.
     */
    public static String getLogFilePath() {
        return POLICY_LOG_FILE;
    }

    /**
     * Print current policy evolution summary to console.
     */
    public static void printSummary(int episodeNumber, Map<String, Double> personality, double totalReward) {
        System.out.println("\n========== POLICY EVOLUTION (Episode " + episodeNumber + ") ==========");
        System.out.println("Timestamp: " + LocalDateTime.now().format(TIME_FORMAT));
        System.out.println("Total Reward: " + String.format("%.3f", totalReward));
        System.out.println("\nPersonality Traits:");
        System.out.println("  Cautious:  " + String.format("%.4f", personality.getOrDefault("cautious", 0.5)));
        System.out.println("  Bold:      " + String.format("%.4f", personality.getOrDefault("bold", 0.5)));
        System.out.println("  Curious:   " + String.format("%.4f", personality.getOrDefault("curious", 0.5)));
        System.out.println("======================================================\n");
    }

    /**
     * Reset the log (clear existing file and start fresh).
     */
    public static void reset() {
        try {
            Files.deleteIfExists(Paths.get(POLICY_LOG_FILE));
            Files.deleteIfExists(Paths.get(REGRET_LOG_FILE));
            headerWritten = false;
            regretHeaderWritten = false;
            System.out.println("[POLICY] Reset: Log files cleared");
        } catch (IOException e) {
            System.err.println("[POLICY] Failed to reset log: " + e.getMessage());
        }
    }

    /**
     * Log CFR cumulative regrets to CSV.
     *
     * @param episodeNumber Current episode number
     * @param regrets Map of strategy names to cumulative regret values
     */
    public static void logRegrets(int episodeNumber, Map<String, Double> regrets) {
        try {
            // Create header if file doesn't exist
            if (!Files.exists(Paths.get(REGRET_LOG_FILE))) {
                writeRegretHeader();
            }

            String timestamp = LocalDateTime.now().format(TIME_FORMAT);

            StringBuilder row = new StringBuilder();
            row.append(timestamp).append(",");
            row.append(episodeNumber).append(",");
            row.append(regrets.getOrDefault("try_new_shop", 0.0)).append(",");
            row.append(regrets.getOrDefault("go_regular_shop", 0.0)).append(",");
            row.append(regrets.getOrDefault("make_at_home", 0.0));

            // Append to file
            Files.write(Paths.get(REGRET_LOG_FILE),
                (row.toString() + System.lineSeparator()).getBytes(),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);

        } catch (IOException e) {
            System.err.println("[POLICY] Failed to log regrets: " + e.getMessage());
        }
    }

    /**
     * Write CSV header for regret log.
     */
    private static void writeRegretHeader() throws IOException {
        String header = "timestamp,episode,try_new_shop,go_regular_shop,make_at_home";
        Files.write(Paths.get(REGRET_LOG_FILE),
            (header + System.lineSeparator()).getBytes(),
            StandardOpenOption.CREATE);
        regretHeaderWritten = true;
        System.out.println("[POLICY] Created regret log: " + REGRET_LOG_FILE);
    }

    /**
     * Get the regret log file path.
     */
    public static String getRegretLogFilePath() {
        return REGRET_LOG_FILE;
    }
}
