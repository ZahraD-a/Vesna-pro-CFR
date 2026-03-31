// Alice: CFR Personality Learning Agent
/* ==========================================
   Coffee Decision: Simple CFR Personality Learning
   ==========================================

   Learning goal: Discover which personality traits lead to success
   through Counterfactual Regret Minimization.

   Scenario: Choosing how to get coffee. 3 plans with different traits.
   The agent learns which personality works best through experience.

   CFR Key Insight:
   - Regret(alternative) = Expected(alt) - Actual(chosen)
   - Personality updates toward traits of high-regret alternatives
   - After many episodes, personality converges to optimal

   3 PLANS with personality traits:
   1. try_new_shop:    bold(0.8), curious(0.7)  → 60% success (risky)
   2. go_regular_shop: cautious(0.8), bold(0.2)  → 85% success (safe)
   3. make_at_home:    cautious(0.9), curious(0.1) → 95% success (safest)
   ========================================== */

// Maximum episodes to run (must match check_done condition)
max_episodes(100).

// Track all three traits in CSV for complete analysis

// Start: Initialize personality and begin
+!start
    <-  .print("=== COFFEE DECISION: CFR PERSONALITY LEARNING ===");
        .print("3 plans with different personality traits."); 
        .print("");
        +episode(0);
        vesna.via.print_personality;
        !episode.

// Episode: 5 decisions → CFR learning at end
+!episode
    :   episode(N)
    <-  .print("--- Episode ", N, " ---");
        !attempt1; !attempt2; !attempt3; !attempt4; !attempt5;
        !attempt6; !attempt7; !attempt8; !attempt9; !attempt10;
        vesna.via.cfr_episode;
        -episode(N);
        N1 = N + 1;
        +episode(N1);
        !check_done.

+!attempt1 <- !decide_coffee.
+!attempt2 <- !decide_coffee.
+!attempt3 <- !decide_coffee.
+!attempt4 <- !decide_coffee.
+!attempt5 <- !decide_coffee.

+!attempt6 <- !decide_coffee.
+!attempt7 <- !decide_coffee.
+!attempt8 <- !decide_coffee.
+!attempt9 <- !decide_coffee.
+!attempt10 <- !decide_coffee.

// Check if we should continue or stop
+!check_done
    :   episode(100)
    <-  .print("\n=== TRAINING COMPLETE ===");
        .print("100 episodes finished.");
        vesna.via.print_personality;
        vesna.via.print_cfr_stats.

+!check_done
    :   episode(N)
    <-  !episode.

/* ==========================================
   DECIDE COFFEE: Choose plan based on personality
   ========================================== */

+!decide_coffee
    <-  -strategy(_); -outcome(_);
        !choose_plan;
        !execute_decision.

/* ==========================================
   3 PLAN OPTIONS with personality traits
   All plans are applicable - agent chooses based on personality similarity
   ========================================== */

// Plan 1: Try new coffee shop (bold + curious = risky exploration)
// Mood Effect: excited(+0.3) - applied when this plan is SELECTED
@try_new_shop[temper([bold(0.8), curious(0.7), cautious(0.2)]), effects([excited(+0.3)[mood]])]
+!choose_plan
    :   true
    <-  .print("Considering: Try the NEW coffee shop");
        .print("  Traits: bold(0.8), curious(0.7), cautious(0.2)");
        .print("  Mood Effect: excited(+0.3) when selected");
        +strategy(try_new_shop).

// Plan 2: Go to regular shop (cautious + some bold = reliable choice)
// Mood Effect: satisfied(+0.2) - applied when this plan is SELECTED
@go_regular_shop[temper([cautious(0.8), bold(0.2), curious(0.3)]), effects([satisfied(+0.2)[mood]])]
+!choose_plan
    :   true
    <-  .print("Considering: Go to the REGULAR coffee shop");
        .print("  Traits: cautious(0.8), bold(0.2), curious(0.3)");
        .print("  Mood Effect: satisfied(+0.2) when selected");
        +strategy(go_regular_shop).

// Plan 3: Make coffee at home (very cautious + low curiosity = safest)
// Mood Effect: content(+0.4) - applied when this plan is SELECTED
@make_at_home[temper([cautious(0.9), curious(0.1), bold(0.1)]), effects([content(+0.4)[mood]])]
+!choose_plan
    :   true
    <-  .print("Considering: Make coffee AT HOME");
        .print("  Traits: cautious(0.9), curious(0.1), bold(0.1)");
        .print("  Mood Effect: content(+0.4) when selected");
        +strategy(make_at_home).

/* ==========================================
   EXECUTE DECISION: Generate outcome based on plan choice

   Success probabilities based on personality traits:
   - try_new_shop:    60% success (bold but risky)
   - go_regular_shop: 85% success (cautious, reliable)
   - make_at_home:    95% success (very cautious, safest)

   CFR will learn that CAUTIOUS trait leads to more success!
   ========================================== */

+!execute_decision
    :   strategy(try_new_shop)
    <-  .random(R);
        .print("  [RNG] try_new_shop random value: ", R);
        !try_new_outcome(R).

+!execute_decision
    :   strategy(go_regular_shop)
    <-  .random(R);
        .print("  [RNG] go_regular_shop random value: ", R);
        !regular_outcome(R).

+!execute_decision
    :   strategy(make_at_home)
    <-  .random(R);
        .print("  [RNG] make_at_home random value: ", R);
        !home_outcome(R).

/* ==========================================
   OUTCOMES: Try new shop (risky exploration)
   ========================================== */

+!try_new_outcome(R)
    :   R < 0.4
    <-  .print("  Outcome: The new place was TERRIBLE! (FAILURE) [R=", R, " < 0.4]");
        +outcome(failure);
        vesna.via.rm_event(failure, -1.0, try_new_shop).

+!try_new_outcome(R)
    :   R >= 0.4
    <-  .print("  Outcome: Found a GREAT new place! (SUCCESS) [R=", R, " >= 0.4]");
        +outcome(success);
        vesna.via.rm_event(success, 1.0, try_new_shop).

/* ==========================================
   OUTCOMES: Go to regular shop (reliable)
   ========================================== */

+!regular_outcome(R)
    :   R < 0.15
    <-  .print("  Outcome: Shop was CLOSED today! (FAILURE) [R=", R, " < 0.15]");
        +outcome(failure);
        vesna.via.rm_event(failure, -1.0, go_regular_shop).

+!regular_outcome(R)
    :   R >= 0.15
    <-  .print("  Outcome: Good coffee as USUAL! (SUCCESS) [R=", R, " >= 0.15]");
        +outcome(success);
        vesna.via.rm_event(success, 1.0, go_regular_shop).

/* ==========================================
   OUTCOMES: Make at home (safest)
   ========================================== */

+!home_outcome(R)
    :   R < 0.05
    <-  .print("  Outcome: Out of coffee beans! (FAILURE) [R=", R, " < 0.05]");
        +outcome(failure);
        vesna.via.rm_event(failure, -1.0, make_at_home).

+!home_outcome(R)
    :   R >= 0.05
    <-  .print("  Outcome: Perfect homemade coffee! (SUCCESS) [R=", R, " >= 0.05]");
        +outcome(success);
        vesna.via.rm_event(success, 1.0, make_at_home).

/* ==========================================
   DEBUG: Test random directly
   ========================================== */

+!test_random
    <-  .random(R);
        .print("Direct random test: R = ", R).
