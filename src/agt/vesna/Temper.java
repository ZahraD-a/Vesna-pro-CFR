package vesna;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.Queue;
import java.util.ArrayList;
import java.util.Random;
import java.util.Iterator;
import java.util.Set;
import java.util.HashSet;
import java.util.stream.Collectors;
import java.io.*;
import java.nio.file.*;
import org.json.JSONObject;

import static jason.asSyntax.ASSyntax.*;
import jason.asSyntax.*;
import jason.asSemantics.*;
import jason.asSyntax.parser.ParseException;
import jason.NoValueException;

/**
 * Temper: personality-driven plan selection with optional CFR learning.
 *
 * <p>The temper of an agent is subdivided into:
 * <ul>
 * <li><b>personality:</b> persistent traits (OCEAN model), updated only by CFR when enabled;
 * <li><b>mood:</b> mutable traits, changed by plan effects annotations.
 * </ul>
 * <p>The agent can apply two decision strategies:
 * <ul>
 * <li><b>Most similar:</b> deterministic, picks plan closest to agent's temper;
 * <li><b>Random:</b> softmax-weighted probabilistic selection.
 * </ul>
 *
 * <p>When CFR learning is enabled, regret matching (adapted from Zinkevich et al. 2008)
 * drives personality evolution at episode boundaries.
 *
 * @author Andrea Gatti (original temper system)
 * @author Zahra Daoui (CFR personality learning extension)
 */
public class Temper {

    // ==================== ORIGINAL VESNA-PRO FIELDS ====================

    private enum DecisionStrategy { MOST_SIMILAR, RANDOM }

    /** Personality: persistent traits [0.0, 1.0] */
    private Map<String, Double> personality;
    /** Mood: mutable traits [-1.0, 1.0] */
    private Map<String, Double> mood;
    /** Decision strategy */
    private DecisionStrategy strategy;
    /** RNG for weighted random selection */
    private Random dice = new Random();

    // ==================== CFR EXTENSION FIELDS ====================

    /** Whether CFR personality learning is enabled (false = static baseline) */
    private boolean cfrEnabled = true;

    /** Trace entry: one decision point with context and outcome */
    public static class TraceEntry {
        public final long timestamp;
        public final String trigger;
        public final List<String> options;
        public final int selectedIndex;
        public final Map<String, Double> personalityAtDecision;
        public final Map<String, Double> moodAtDecision;
        public final List<Double> weights;
        public final List<Map<String, Double>> planAnnotations;
        public double reward = 0.0;

        TraceEntry(String trig, List<String> opts, int sel,
                   Map<String, Double> pers, Map<String, Double> mod,
                   List<Double> wts, List<Map<String, Double>> annotations) {
            timestamp = System.currentTimeMillis();
            trigger = trig;
            options = new ArrayList<>(opts);
            selectedIndex = sel;
            personalityAtDecision = new HashMap<>(pers);
            moodAtDecision = new HashMap<>(mod);
            weights = new ArrayList<>(wts);
            planAnnotations = new ArrayList<>();
            for (Map<String, Double> ann : annotations) {
                planAnnotations.add(new HashMap<>(ann));
            }
        }

        @Override
        public String toString() {
            return "Trace[" + trigger + ": selected=" + options.get(selectedIndex)
                + " reward=" + reward + "]";
        }
    }

    private List<TraceEntry> trace = new ArrayList<>();
    private Map<String, Double> cumulativeRegret = new HashMap<>();
    private double cfrLearningRate = 0.5;
    private double softmaxTemperature = 2.0;
    private static final double TEMPERATURE_DECAY = 0.995;
    private static final double MIN_TEMPERATURE = 0.5;
    private static final String PERSONALITY_FILE = "personality.json";

    /** Behavioral memory (extracted to separate class) */
    private BehavioralMemory behavioralMemory = new BehavioralMemory();

    /** CFR data for an information set (decision point). */
    public static class InformationSet {
        public final String name;
        public final Map<String, Double> cumulativeRegret;
        public final Map<String, Double> strategySum;
        public int visitCount;

        public InformationSet(String name) {
            this.name = name;
            this.cumulativeRegret = new HashMap<>();
            this.strategySum = new HashMap<>();
            this.visitCount = 0;
        }
    }

    private Map<String, InformationSet> informationSets = new HashMap<>();
    private List<TraceEntry> currentEpisodeDecisions = new ArrayList<>();
    private Map<String, Double> stageRewards = new HashMap<>();
    private double totalEpisodeReward = 0.0;

    private InformationSet getInformationSet(String name) {
        return informationSets.computeIfAbsent(name, InformationSet::new);
    }

    /** Normalize plan labels: strip quotes and handle Jason duplicates. */
    private String normalizePlanLabel(String label) {
        if (label == null) return null;
        String cleaned = label.replaceAll("^\"|\"$", "");
        if (cleaned.matches("p__\\d+")) return "p2";
        return cleaned;
    }

    // ==================== HISTORICAL PERFORMANCE ====================

    private Map<String, Double> planTotalReward = new HashMap<>();
    private Map<String, Integer> planAttempts = new HashMap<>();

    private void updateHistoricalPerformance(String plan, double reward) {
        planTotalReward.put(plan, planTotalReward.getOrDefault(plan, 0.0) + reward);
        planAttempts.put(plan, planAttempts.getOrDefault(plan, 0) + 1);
    }

    /** Get historical average reward for a plan. Returns 0.0 if no data. */
    private double getHistoricalAverage(String plan) {
        int attempts = planAttempts.getOrDefault(plan, 0);
        if (attempts == 0) return 0.0;
        return planTotalReward.getOrDefault(plan, 0.0) / attempts;
    }

    // ==================== CONSTRUCTORS ====================

    /** Original constructor (backward-compatible). */
    public Temper(String temper, String strategy) throws IllegalArgumentException {
        this(temper, strategy, -1, true);
    }

    /** Extended constructor with seed and CFR control. */
    public Temper(String temper, String strategy, long seed, boolean cfrEnabled)
            throws IllegalArgumentException {
        if (temper == null)
            throw new IllegalArgumentException("Temper cannot be null");

        personality = new HashMap<>();
        mood = new HashMap<>();
        cumulativeRegret = new HashMap<>();
        this.cfrEnabled = cfrEnabled;
        if (seed >= 0) {
            this.dice = new Random(seed);
            System.out.println("[TEMPER] Using fixed seed: " + seed);
        }

        try {
            Literal listLit = parseLiteral(temper);
            for (Term term : listLit.getTerms()) {
                Literal trait = (Literal) term;
                double value = (double) ((NumberTerm) trait.getTerm(0)).solve();
                if (trait.hasAnnot(createLiteral("mood"))) {
                    if (value < -1.0 || value > 1.0)
                        throw new IllegalArgumentException(
                            "Mood value must be in [-1, 1], found: " + trait);
                    mood.put(trait.getFunctor().toString(), value);
                } else {
                    if (value < 0.0 || value > 1.0)
                        throw new IllegalArgumentException(
                            "Personality value must be in [0, 1], found: " + trait);
                    personality.put(trait.getFunctor().toString(), value);
                }
            }
        } catch (ParseException pe) {
            throw new IllegalArgumentException(pe.getMessage());
        } catch (NoValueException nve) {
            throw new IllegalArgumentException(nve.getMessage());
        }

        if (strategy == null)
            this.strategy = DecisionStrategy.MOST_SIMILAR;
        else if (strategy.equals("most_similar"))
            this.strategy = DecisionStrategy.MOST_SIMILAR;
        else if (strategy.equals("random"))
            this.strategy = DecisionStrategy.RANDOM;
        else
            throw new IllegalArgumentException("Unknown strategy: " + strategy);
    }

    // ==================== ORIGINAL: WEIGHT COMPUTATION ====================

    /**
     * Compute weight for a plan based on personality similarity.
     * RANDOM strategy: dot product (higher = more similar)
     * MOST_SIMILAR strategy: absolute distance (lower = more similar)
     */
    public double computeWeight(Pred label) throws NoValueException {
        double choiceWeight = 0;

        Literal temperAnnot = label.getAnnot("temper");
        if (temperAnnot == null)
            return choiceWeight;

        ListTerm choiceTemper = (ListTerm) temperAnnot.getTerm(0);
        for (Term traitTerm : choiceTemper) {
            Atom trait = (Atom) traitTerm;
            String traitName = trait.getFunctor().toString();

            if (!mood.containsKey(traitName) && !personality.containsKey(traitName))
                continue;

            double traitTemper;
            if (mood.containsKey(traitName))
                traitTemper = mood.get(traitName);
            else
                traitTemper = personality.get(traitName);

            double traitValue = (double) ((NumberTerm) trait.getTerm(0)).solve();
            if (traitValue < -1.0 || traitValue > 1.0)
                throw new IllegalArgumentException(
                    "Trait value out of range: " + trait);

            if (strategy == DecisionStrategy.RANDOM)
                choiceWeight += traitTemper * traitValue;
            else if (strategy == DecisionStrategy.MOST_SIMILAR)
                choiceWeight += Math.abs(traitTemper - traitValue);
        }
        return choiceWeight;
    }

    // ==================== ORIGINAL: PLAN / INTENTION SELECTION ====================

    public boolean hasOptionsAnnotation(List<Option> options) {
        List<OptionWrapper> wrappedOptions = options.stream()
            .map(OptionWrapper::new)
            .collect(Collectors.toList());
        return hasAnnotation(wrappedOptions);
    }

    public boolean hasIntentionsAnnotation(Queue<Intention> intentions) {
        List<IntentionWrapper> wrappedIntentions = intentions.stream()
            .map(IntentionWrapper::new)
            .collect(Collectors.toList());
        return hasAnnotation(wrappedIntentions);
    }

    private <T extends TemperSelectable> boolean hasAnnotation(List<T> choices) {
        Literal annotPattern = createLiteral("temper", new VarTerm("X"));
        for (T choice : choices) {
            Pred l = choice.getLabel();
            if (l.hasAnnot()) {
                for (Term t : l.getAnnots()) {
                    if (new Unifier().unifies(annotPattern, t))
                        return true;
                }
            }
        }
        return false;
    }

    public Option selectOption(List<Option> options) {
        List<OptionWrapper> wrappedOptions = options.stream()
            .map(OptionWrapper::new)
            .collect(Collectors.toList());
        try {
            return select(wrappedOptions).getOption();
        } catch (NoValueException e) {
            return null;
        }
    }

    public Intention selectIntention(Queue<Intention> intentions) {
        List<IntentionWrapper> wrappedIntentions = new ArrayList<>(intentions).stream()
            .map(IntentionWrapper::new)
            .collect(Collectors.toList());
        try {
            Intention selected = select(wrappedIntentions).getIntention();
            Iterator<Intention> it = intentions.iterator();
            while (it.hasNext()) {
                if (it.next() == selected) {
                    it.remove();
                    break;
                }
            }
            Literal effectList = selected.peek().getPlan().getLabel().getAnnot("effects");
            if (effectList != null)
                updateDynTemper(effectList);
            return selected;
        } catch (NoValueException e) {
            return null;
        }
    }

    public <T extends TemperSelectable> T select(List<T> choices) throws NoValueException {
        List<Double> weights = new ArrayList<>();
        for (T choice : choices) {
            weights.add(computeWeight(choice.getLabel()));
        }

        T chosen = null;
        int chosenIdx = -1;
        if (strategy == DecisionStrategy.RANDOM) {
            chosenIdx = getWeightedRandomIdx(weights);
            chosen = choices.get(chosenIdx);
        } else if (strategy == DecisionStrategy.MOST_SIMILAR) {
            chosenIdx = getMostSimilarIdx(weights);
            chosen = choices.get(chosenIdx);
        }
        if (chosen == null) {
            chosenIdx = 0;
            chosen = choices.get(chosenIdx);
        }

        // CFR extension: record decision only when CFR is active
        if (cfrEnabled) {
            recordDecision(choices, chosenIdx, weights);
        }

        return chosen;
    }

    // ==================== CFR: DECISION CONTEXT ====================

    private String currentStage = "root";

    public void setCurrentStage(String stage) {
        this.currentStage = stage;
    }

    /** Record a decision in the current episode for CFR learning. */
    private <T extends TemperSelectable> void recordDecision(
            List<T> choices, int selectedIdx, List<Double> weights) {

        List<String> optionLabels = choices.stream()
            .map(c -> normalizePlanLabel(c.getLabel().getFunctor()))
            .collect(Collectors.toList());

        // Extract plan annotations
        List<Map<String, Double>> annotations = new ArrayList<>();
        for (T choice : choices) {
            Map<String, Double> planTraits = new HashMap<>();
            Literal annot = choice.getLabel().getAnnot("temper");
            if (annot != null) {
                ListTerm traits = (ListTerm) annot.getTerm(0);
                for (Term traitTerm : traits) {
                    Literal trait = (Literal) traitTerm;
                    try {
                        double value = ((NumberTerm) trait.getTerm(0)).solve();
                        planTraits.put(trait.getFunctor(), value);
                    } catch (NoValueException e) {
                        // Skip invalid traits
                    }
                }
            }
            annotations.add(planTraits);
        }

        TraceEntry entry = new TraceEntry(currentStage, optionLabels, selectedIdx,
            new HashMap<>(personality), new HashMap<>(mood), weights, annotations);
        currentEpisodeDecisions.add(entry);

        InformationSet infoset = getInformationSet(currentStage);
        infoset.visitCount++;
        String chosenAction = optionLabels.get(selectedIdx);
        infoset.strategySum.put(chosenAction,
            infoset.strategySum.getOrDefault(chosenAction, 0.0) + 1.0);

        double[] probs = computeActionProbabilities(weights);

        StringBuilder sb = new StringBuilder();
        sb.append("[CFR] Stage=").append(currentStage)
          .append(" Decision #").append(currentEpisodeDecisions.size()).append(":\n");
        for (int i = 0; i < optionLabels.size(); i++) {
            sb.append("    ").append(optionLabels.get(i))
              .append(": weight=").append(String.format("%.3f", weights.get(i)))
              .append(", prob=").append(String.format("%.1f%%", probs[i] * 100));
            if (i == selectedIdx) sb.append(" <-- SELECTED");
            sb.append("\n");
        }
        System.out.print(sb.toString());
    }

    // ==================== CFR: RECORD OUTCOME ====================

    /**
     * Record outcome using regret matching adapted from CFR.
     *
     * @param action The action taken (e.g., "help_bob")
     * @param reward The actual reward received (after behavioral memory adjustment)
     * @param person The person involved (bob, carol, dave)
     */
    public void recordHelpOutcome(String action, double reward, String person) {

        // Set reward in most recent trace entry matching this stage
        String expectedStage = "help_" + person;
        if (!currentEpisodeDecisions.isEmpty()) {
            for (int i = currentEpisodeDecisions.size() - 1; i >= 0; i--) {
                TraceEntry entry = currentEpisodeDecisions.get(i);
                if (expectedStage.equals(entry.trigger) && entry.reward == 0.0) {
                    entry.reward = reward;
                    break;
                }
            }
        }

        // Get information set for this person (already created in recordDecision)
        String infosetName = "help_" + person;
        InformationSet infoset = getInformationSet(infosetName);
        // Note: visitCount already incremented in recordDecision — do NOT increment again

        // Update historical performance
        updateHistoricalPerformance(action, reward);

        System.out.println("\n[CFR] " + person.toUpperCase() + " - " + action
            + " -> reward=" + String.format("%.3f", reward));

        // Standard CFR: compute regrets for all actions
        String[] allActions = HelpScenarioConfig.getActionsForPerson(person);
        double expectedChosen = getHistoricalAverage(action);

        for (String alt : allActions) {
            double expectedAlt = getHistoricalAverage(alt);
            double regret;

            if (alt.equals(action)) {
                regret = 0.0;
            } else {
                regret = expectedAlt - expectedChosen;
            }

            double currentRegret = infoset.cumulativeRegret.getOrDefault(alt, 0.0);
            infoset.cumulativeRegret.put(alt, currentRegret + regret);

            if (regret != 0 || alt.equals(action)) {
                String sign = regret > 0 ? "+" : "";
                System.out.println(String.format(
                    "  Regret(%s) = E[%.3f] - E[%.3f] = %s%.3f (cumulative: %.3f)",
                    alt, expectedAlt, expectedChosen, sign, regret,
                    currentRegret + regret));
            }
        }

        totalEpisodeReward += reward;
    }

    // ==================== CFR: PERSONALITY UPDATE ====================

    /**
     * Update OCEAN personality traits via CFR regret matching.
     *
     * For each information set (per person):
     *   1. Find actions with positive cumulative regret
     *   2. Compute regret weights: w(a) = R+(a) / sum(R+)
     *   3. Compute gradient: grad(trait) = sum_a[ w(a) * (action_trait - current) ]
     *   4. Apply: new = old + learning_rate * gradient, clamped to [0, 1]
     */
    public void updatePersonalityFromCFR() {
        if (currentEpisodeDecisions.isEmpty()) return;
        if (!cfrEnabled) {
            System.out.println("[CFR] Learning DISABLED (static baseline mode)");
            return;
        }

        System.out.println("\n========== CFR: PERSONALITY UPDATE ==========");

        Map<String, Double> traitGradients = new HashMap<>();
        for (String trait : personality.keySet()) {
            traitGradients.put(trait, 0.0);
        }

        int infosetCount = 0;

        for (InformationSet infoset : informationSets.values()) {
            if (infoset.cumulativeRegret.isEmpty()) continue;

            double totalPositiveRegret = 0.0;
            for (Double r : infoset.cumulativeRegret.values()) {
                if (r > 0) totalPositiveRegret += r;
            }

            if (totalPositiveRegret < 0.001) continue;
            infosetCount++;

            System.out.println("\n  [" + infoset.name + "] Regrets:");

            for (Map.Entry<String, Double> entry : infoset.cumulativeRegret.entrySet()) {
                String action = entry.getKey();
                double regret = entry.getValue();

                System.out.println("    " + action + ": "
                    + String.format("%.3f", regret)
                    + (regret > 0 ? " (positive)" : ""));

                if (regret <= 0) continue;

                double regretWeight = regret / totalPositiveRegret;
                Map<String, Double> actionTraits = HelpScenarioConfig.getActionTraits(action);
                if (actionTraits == null) continue;

                for (Map.Entry<String, Double> traitEntry : actionTraits.entrySet()) {
                    String traitName = traitEntry.getKey();
                    double actionValue = traitEntry.getValue();
                    double currentValue = personality.getOrDefault(traitName, 0.5);
                    double gradient = regretWeight * (actionValue - currentValue);

                    traitGradients.put(traitName,
                        traitGradients.getOrDefault(traitName, 0.0) + gradient);
                }
            }
        }

        if (infosetCount > 0) {
            System.out.println("\n  Applying updates (lr=" + cfrLearningRate + "):");
            for (String trait : traitGradients.keySet()) {
                double gradient = traitGradients.get(trait);
                if (Math.abs(gradient) < 0.001) continue;

                double oldValue = personality.getOrDefault(trait, 0.5);
                double newValue = oldValue + cfrLearningRate * gradient;
                newValue = Math.max(0.0, Math.min(1.0, newValue));
                personality.put(trait, newValue);

                System.out.println("    " + trait + ": "
                    + String.format("%.3f", oldValue)
                    + " -> " + String.format("%.3f", newValue)
                    + " (gradient=" + String.format("%+.4f", gradient) + ")");
            }
        } else {
            System.out.println("  No positive regrets — personality unchanged");
        }

        System.out.println("=============================================\n");
    }

    // ==================== EPISODE MANAGEMENT ====================

    /** End episode: trigger CFR learning, save, reset episode state. */
    public void startNewEpisode() {
        System.out.println("[CFR] Episode complete. Decisions: "
            + currentEpisodeDecisions.size()
            + ", Total reward: " + String.format("%.2f", totalEpisodeReward));

        System.out.println("[CFR] Personality BEFORE: " + formatPersonality());
        updatePersonalityFromCFR();
        System.out.println("[CFR] Personality AFTER:  " + formatPersonality());

        savePersonality();

        // Reset episode state (but KEEP cumulative regrets for convergence)
        currentEpisodeDecisions.clear();
        stageRewards.clear();
        totalEpisodeReward = 0.0;
        currentStage = "root";

        // Decay exploration temperature
        softmaxTemperature = Math.max(MIN_TEMPERATURE, softmaxTemperature * TEMPERATURE_DECAY);
        System.out.println("[CFR] Regrets preserved. Temperature=" + String.format("%.3f", softmaxTemperature));
    }

    private String formatPersonality() {
        StringBuilder sb = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, Double> entry : personality.entrySet()) {
            if (!first) sb.append(" ");
            sb.append(entry.getKey()).append("=")
              .append(String.format("%.3f", entry.getValue()));
            first = false;
        }
        sb.append("}");
        return sb.toString();
    }

    // ==================== CFR STATS ====================

    /** Print CFR statistics for all information sets. */
    public void printCFRStats() {
        System.out.println("\n==================== CFR STATISTICS ====================");

        System.out.println("\n  Information Sets: " + informationSets.size());
        for (Map.Entry<String, InformationSet> entry : informationSets.entrySet()) {
            InformationSet infoset = entry.getValue();
            System.out.println("\n  [" + infoset.name + "] visited "
                + infoset.visitCount + " times");

            if (!infoset.cumulativeRegret.isEmpty()) {
                System.out.println("    Cumulative Regrets:");
                double totalPos = 0.0;
                for (Double r : infoset.cumulativeRegret.values()) {
                    if (r > 0) totalPos += r;
                }
                for (Map.Entry<String, Double> regret : infoset.cumulativeRegret.entrySet()) {
                    double r = regret.getValue();
                    String pct = totalPos > 0 && r > 0
                        ? String.format(" (%.1f%%)", r / totalPos * 100) : "";
                    System.out.println("      " + regret.getKey() + ": "
                        + String.format("%.3f", r) + pct);
                }
            }

            if (!infoset.strategySum.isEmpty()) {
                System.out.println("    Average Strategy:");
                for (Map.Entry<String, Double> strat : infoset.strategySum.entrySet()) {
                    double avg = strat.getValue() / Math.max(1, infoset.visitCount);
                    System.out.println("      " + strat.getKey() + ": "
                        + String.format("%.3f", avg));
                }
            }
        }

        // Print historical performance
        if (!planAttempts.isEmpty()) {
            System.out.println("\n  Historical Performance:");
            for (String plan : planAttempts.keySet()) {
                int attempts = planAttempts.get(plan);
                if (attempts > 0) {
                    double avg = planTotalReward.getOrDefault(plan, 0.0) / attempts;
                    System.out.println(String.format("    %s: %d attempts, avg=%.3f",
                        plan, attempts, avg));
                }
            }
        }

        System.out.println("\n========================================================\n");
    }

    // ==================== CUMULATIVE REGRETS (for logging) ====================

    /** Get cumulative regrets across all information sets (for PolicyLogger). */
    public Map<String, Double> getHelpCumulativeRegrets() {
        Map<String, Double> regrets = new HashMap<>();
        for (String action : HelpScenarioConfig.getAllActionTraits().keySet()) {
            regrets.put(action, 0.0);
        }
        for (InformationSet infoset : informationSets.values()) {
            for (Map.Entry<String, Double> entry : infoset.cumulativeRegret.entrySet()) {
                String action = entry.getKey();
                regrets.put(action, regrets.getOrDefault(action, 0.0) + entry.getValue());
            }
        }
        return regrets;
    }

    // ==================== BEHAVIORAL MEMORY DELEGATION ====================

    /** Initialize behavioral memory for the help scenario. */
    public void initBehavioralMemory() {
        HelpScenarioConfig.initBehavioralMemory(behavioralMemory);
    }

    /** Update behavioral memory after an interaction. */
    public void updateBehavioralMemory(String person, boolean helped) {
        behavioralMemory.update(person, helped, dice);
    }

    /** Get behavioral memory value for a person. */
    public double getBehavioralValue(String person, String metric) {
        return behavioralMemory.getValue(person, metric);
    }

    // ==================== PERSONALITY PERSISTENCE ====================

    /** Save personality to JSON file. */
    private void savePersonality() {
        try {
            JSONObject persJson = new JSONObject();
            for (Map.Entry<String, Double> e : personality.entrySet()) {
                persJson.put(e.getKey(), Math.round(e.getValue() * 1000.0) / 1000.0);
            }
            JSONObject moodJson = new JSONObject();
            for (Map.Entry<String, Double> e : mood.entrySet()) {
                moodJson.put(e.getKey(), Math.round(e.getValue() * 1000.0) / 1000.0);
            }
            JSONObject root = new JSONObject();
            root.put("personality", persJson);
            root.put("mood", moodJson);

            Files.writeString(Path.of(PERSONALITY_FILE), root.toString(2));
        } catch (IOException e) {
            System.err.println("[PERSIST] Failed to save: " + e.getMessage());
        }
    }

    /** Load personality from JSON file. */
    public static Map<String, Object> loadPersonalityFromFile() {
        try {
            File f = new File(PERSONALITY_FILE);
            if (!f.exists()) return null;

            String content = Files.readString(Path.of(PERSONALITY_FILE));
            System.out.println("[PERSIST] Loaded personality from " + PERSONALITY_FILE);

            JSONObject root = new JSONObject(content);
            Map<String, Object> result = new HashMap<>();

            Map<String, Double> persMap = new HashMap<>();
            if (root.has("personality")) {
                JSONObject persJson = root.getJSONObject("personality");
                for (String key : persJson.keySet()) {
                    persMap.put(key, persJson.getDouble(key));
                }
            }
            result.put("personality", persMap);

            Map<String, Double> moodMap = new HashMap<>();
            if (root.has("mood")) {
                JSONObject moodJson = root.getJSONObject("mood");
                for (String key : moodJson.keySet()) {
                    moodMap.put(key, moodJson.getDouble(key));
                }
            }
            result.put("mood", moodMap);

            return result;
        } catch (Exception e) {
            System.err.println("[PERSIST] Failed to load: " + e.getMessage());
            return null;
        }
    }

    // ==================== GETTERS ====================

    public static String getPersonalityFile() { return PERSONALITY_FILE; }
    public Map<String, Double> getPersonality() { return new HashMap<>(personality); }
    public Map<String, Double> getMood() { return new HashMap<>(mood); }
    public double getTotalEpisodeReward() { return totalEpisodeReward; }
    public List<TraceEntry> getTrace() { return new ArrayList<>(currentEpisodeDecisions); }

    // ==================== SOFTMAX & SELECTION HELPERS ====================

    /** Softmax normalization with temperature annealing for exploration control. */
    private double[] computeActionProbabilities(List<Double> weights) {
        double[] probs = new double[weights.size()];
        double minWeight = Double.MAX_VALUE;
        for (double w : weights) minWeight = Math.min(minWeight, w);

        double sum = 0.0;
        for (int i = 0; i < weights.size(); i++) {
            probs[i] = Math.exp((weights.get(i) - minWeight) / softmaxTemperature);
            sum += probs[i];
        }

        if (sum > 0) {
            for (int i = 0; i < probs.length; i++) probs[i] /= sum;
        } else {
            for (int i = 0; i < probs.length; i++) probs[i] = 1.0 / probs.length;
        }
        return probs;
    }

    private int getWeightedRandomIdx(List<Double> weights) {
        double[] probs = computeActionProbabilities(weights);
        double[] cumulative = new double[weights.size()];
        double total = 0.0;
        for (int i = 0; i < weights.size(); i++) {
            total += probs[i];
            cumulative[i] = total;
        }

        double roll = dice.nextDouble();

        StringBuilder sb = new StringBuilder("[RANDOM] roll=")
            .append(String.format("%.3f", roll)).append(" cumulative=");
        for (int i = 0; i < cumulative.length; i++) {
            sb.append(String.format("%.3f", cumulative[i]));
            if (i < cumulative.length - 1) sb.append(", ");
        }
        System.out.println(sb.toString());

        for (int i = 0; i < cumulative.length; i++) {
            if (roll < cumulative[i]) return i;
        }
        return weights.size() - 1;
    }

    private int getMostSimilarIdx(List<Double> weights) {
        double min = Double.MAX_VALUE;
        int minIdx = -1;
        for (int i = 0; i < weights.size(); i++) {
            if (weights.get(i) < min) {
                min = weights.get(i);
                minIdx = i;
            }
        }
        return minIdx;
    }

    // ==================== ORIGINAL: MOOD EFFECTS ====================

    /** Apply mood effects from plan annotation (called by selectIntention). */
    private void updateDynTemper(Literal effectList) throws NoValueException {
        ListTerm effects = (ListTerm) effectList.getTerm(0);
        for (Term effectTerm : effects) {
            Literal effect = (Literal) effectTerm;
            String effectName = effect.getFunctor().toString();

            if (personality.containsKey(effectName) && !effect.hasAnnot(createLiteral("mood")))
                throw new IllegalArgumentException(
                    "Cannot use personality trait '" + effectName + "' in effects. Use mood traits only.");

            if (mood.get(effectName) == null) continue;

            double moodValue = mood.get(effectName);
            double effectValue = (double) ((NumberTerm) effect.getTerm(0)).solve();

            if (effectValue < -1.0 || effectValue > 1.0)
                throw new IllegalArgumentException(
                    "Effect value out of range: " + effectValue);

            double newMood = Math.max(-1.0, Math.min(1.0, moodValue + effectValue));
            mood.put(effectName, newMood);

            System.out.println("[TEMPER] Mood: " + effectName + " "
                + String.format("%.2f", moodValue) + " -> "
                + String.format("%.2f", newMood));
        }
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("[TEMPER] Personality: ");
        personality.forEach((k, v) -> sb.append(k + "=" + String.format("%.2f", v) + " "));
        sb.append("| Mood: ");
        mood.forEach((k, v) -> sb.append(k + "=" + String.format("%.2f", v) + " "));
        return sb.toString();
    }

}
