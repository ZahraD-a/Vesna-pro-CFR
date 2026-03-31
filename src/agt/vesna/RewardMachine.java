package vesna;

import java.util.*;

/**
 * Simple Reward Tracker for CFR-based personality learning.
 *
 * <p>CONCEPT:</p>
 * <pre>
 *   Total Reward = Base Reward + Personality Alignment Bonus
 *
 *   Base Reward:
 *     - Success:  +1.0
 *     - Failure:  -1.0
 *
 *   Alignment Bonus:
 *     - Measures how well the plan matches the agent's personality
 *     - Range: -0.5 to +0.5
 *     - Plans that match personality AND succeed get higher rewards
 *     - This teaches the agent which personality traits work well
 * </pre>
 *
 * <p>EXAMPLE:</p>
 * <pre>
 *   Plan p1 has traits [aggressive(0.9), cautious(0.1)]
 *   Agent has personality [aggressive(0.8), cautious(0.2)]
 *
 *   If p1 succeeds:
 *     Base reward:      +1.0
 *     Alignment bonus:  +0.4 (high match)
 *     Total:            +1.4
 *
 *   If p1 fails:
 *     Base reward:      -1.0
 *     Alignment bonus:  +0.4 (still matched personality)
 *     Total:            -0.6
 * </pre>
 *
 * @author VesnaPro CFR Extension
 */
public class RewardMachine {

    // ========================= REWARD VALUES (EASILY ADJUSTABLE) =========================

    /** Base reward for successful plan execution */
    public static final double BASE_REWARD_SUCCESS = +1.0;

    /** Base penalty for failed plan execution */
    public static final double BASE_REWARD_FAILURE = -1.0;

    /** Maximum bonus for personality alignment (can be positive or negative) */
    public static final double MAX_ALIGNMENT_BONUS = 0.5;

    // ========================= EVENT TYPES =========================

    /**
     * Events that generate rewards.
     * Simplified to just success or failure - everything else is noise.
     */
    public enum Event {
        /** Plan executed successfully - positive outcome */
        SUCCESS,

        /** Plan failed to execute - negative outcome */
        FAILURE
    }

    // ========================= INSTANCE VARIABLES =========================

    /** Total reward accumulated in current episode */
    private double accumulatedReward;

    /** Number of successful plans */
    private int successCount;

    /** Number of failed plans */
    private int failureCount;

    /** Reward history for CFR learning - stores each reward with context */
    private List<RewardEntry> rewardHistory;

    /** Reference to agent's Temper for computing alignment */
    private Temper temper;

    // ========================= REWARD ENTRY (for CFR) =========================

    /**
     * Records a single reward event for later CFR analysis.
     */
    public static class RewardEntry {
        public final long timestamp;
        public final Event event;
        public final double baseReward;
        public final double alignmentBonus;
        public final double totalReward;
        public final String planLabel;

        RewardEntry(Event evt, double base, double bonus, String label) {
            this.timestamp = System.currentTimeMillis();
            this.event = evt;
            this.baseReward = base;
            this.alignmentBonus = bonus;
            this.totalReward = base + bonus;
            this.planLabel = label;
        }

        @Override
        public String toString() {
            return String.format("RewardEntry[%s: base=%.2f, bonus=%.2f, total=%.2f, plan=%s]",
                    event, baseReward, alignmentBonus, totalReward, planLabel);
        }
    }

    // ========================= CONSTRUCTOR =========================

    /**
     * Creates a new RewardMachine.
     */
    public RewardMachine() {
        this.accumulatedReward = 0.0;
        this.successCount = 0;
        this.failureCount = 0;
        this.rewardHistory = new ArrayList<>();
    }

    /**
     * Sets the Temper reference for computing personality alignment.
     * Must be called before computing rewards with alignment.
     */
    public void setTemper(Temper temper) {
        this.temper = temper;
    }

    // ========================= CORE REWARD METHOD =========================

    /**
     * Main method: Compute and record a reward for a plan outcome.
     *
     * <p>Formula: reward = base + alignment_bonus</p>
     *
     * @param event SUCCESS or FAILURE
     * @param planLabel The name/label of the plan (e.g., "p1", "go_to_coffee")
     * @param planTraits The personality traits of the plan (from annotation)
     * @return The total reward (base + alignment)
     */
    public double computeReward(Event event, String planLabel, Map<String, Double> planTraits) {
        // Step 1: Get base reward based on outcome
        double baseReward = getBaseReward(event);

        // Step 2: Compute alignment bonus (how well plan matches agent's personality)
        double alignmentBonus = 0.0;
        if (temper != null && planTraits != null && !planTraits.isEmpty()) {
            alignmentBonus = computeAlignmentBonus(planTraits) * MAX_ALIGNMENT_BONUS;
        }

        // Step 3: Total reward
        double totalReward = baseReward + alignmentBonus;

        // Step 4: Record statistics
        accumulatedReward += totalReward;
        if (event == Event.SUCCESS) {
            successCount++;
        } else {
            failureCount++;
        }

        // Step 5: Save to history for CFR
        rewardHistory.add(new RewardEntry(event, baseReward, alignmentBonus, planLabel));

        // Step 6: Print clear output
        System.out.println(String.format(
                "[REWARD] %s executed plan '%s': base=%.2f, alignment=%.2f, total=%.2f",
                event, planLabel, baseReward, alignmentBonus, totalReward));

        return totalReward;
    }

    /**
     * Simplified version when you don't have plan traits available.
     * Just uses base reward without alignment bonus.
     */
    public double computeReward(Event event, String planLabel) {
        return computeReward(event, planLabel, null);
    }

    // ========================= HELPER METHODS =========================

    /**
     * Get the base reward for an event type.
     */
    private double getBaseReward(Event event) {
        switch (event) {
            case SUCCESS:
                return BASE_REWARD_SUCCESS;
            case FAILURE:
                return BASE_REWARD_FAILURE;
            default:
                return 0.0;
        }
    }

    /**
     * Compute how well a plan's traits match the agent's personality.
     *
     * <p>Returns a value between -1.0 and +1.0:</p>
     * <ul>
     *   <li>+1.0 = Perfect match (plan traits = agent personality)</li>
     *   <li>0.0 = No correlation</li>
     *   <li>-1.0 = Perfect mismatch</li>
     * </ul>
     *
     * <p>Uses cosine similarity for the computation.</p>
     */
    private double computeAlignmentBonus(Map<String, Double> planTraits) {
        if (temper == null) return 0.0;

        Map<String, Double> agentPersonality = temper.getPersonality();
        if (agentPersonality == null || agentPersonality.isEmpty()) return 0.0;

        // Cosine similarity: (A . B) / (|A| * |B|)
        double dotProduct = 0.0;
        double normA = 0.0;
        double normB = 0.0;

        // Get all traits from both plan and agent
        Set<String> allTraits = new HashSet<>();
        allTraits.addAll(planTraits.keySet());
        allTraits.addAll(agentPersonality.keySet());

        for (String trait : allTraits) {
            double planValue = planTraits.getOrDefault(trait, 0.0);
            double agentValue = agentPersonality.getOrDefault(trait, 0.0);

            dotProduct += planValue * agentValue;
            normA += planValue * planValue;
            normB += agentValue * agentValue;
        }

        // Avoid division by zero
        if (normA == 0.0 || normB == 0.0) return 0.0;

        return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
    }

    // ========================= GETTERS =========================

    /** Get total accumulated reward for current episode */
    public double getAccumulatedReward() {
        return accumulatedReward;
    }

    /** Get number of successful plans */
    public int getSuccessCount() {
        return successCount;
    }

    /** Get number of failed plans */
    public int getFailureCount() {
        return failureCount;
    }

    /** Get success rate (0.0 to 1.0) */
    public double getSuccessRate() {
        int total = successCount + failureCount;
        return total == 0 ? 0.0 : (double) successCount / total;
    }

    /** Get all reward history for CFR analysis */
    public List<RewardEntry> getRewardHistory() {
        return new ArrayList<>(rewardHistory);
    }

    /** Clear history and reset for new episode */
    public void reset() {
        accumulatedReward = 0.0;
        successCount = 0;
        failureCount = 0;
        rewardHistory.clear();
        System.out.println("[REWARD] Reset for new episode");
    }

    // ========================= SUMMARY FOR DISPLAY =========================

    @Override
    public String toString() {
        return String.format(
                "[REWARD] total=%.2f | success=%d | failure=%d | rate=%.1f%%",
                accumulatedReward,
                successCount,
                failureCount,
                getSuccessRate() * 100);
    }

    /**
     * Print a detailed summary of the episode.
     */
    public void printSummary() {
        System.out.println("\n========== REWARD SUMMARY ==========");
        System.out.println(this);
        System.out.println("====================================\n");
    }
}
