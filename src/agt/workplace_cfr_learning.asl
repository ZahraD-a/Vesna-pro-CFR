// Help Scenario: CFR Personality Learning with OCEAN Traits
/* ==========================================
   WORKPLACE HELP-SEEKING: CFR Personality Learning

   Agent: Alice — a mid-level developer
   Learns which OCEAN personality traits lead to successful
   social interactions via Counterfactual Regret Minimization.
 
   Characters:
   - Bob:   Senior Developer — demanding but fair, moderate reciprocity
   - Carol: Junior Developer — asks often, rarely reciprocates (exploitative)
   - Dave:  Product Manager  — appreciative, vocal, highly reciprocal

   Key design:
   - Plans are OCEAN-annotated → Temper.select() does softmax selection
   - Base rewards are uniform (+0.5 success, -0.3 failure)
   - Behavioral memory creates reward divergence over time
   - CFR updates personality toward traits of high-regret actions
   ========================================== */

interactions_per_colleague(10).
max_episodes(2000).

// ==========================================
// INITIALIZATION
// ==========================================

+!start
    <-  .print("=== WORKPLACE HELP-SEEKING: CFR PERSONALITY LEARNING ===");
        .print("Agent: Alice | Colleagues: Bob (senior), Carol (junior), Dave (PM)");
        .print("OCEAN traits guide plan selection. CFR learns optimal personality.");
        .print("");
        vesna.via.init_behavioral_memory;
        vesna.via.print_personality;
        +episode(0);
        !episode.

// ==========================================
// EPISODE LOOP
// ==========================================

+!episode
    :   episode(N) & interactions_per_colleague(K)
    <-  .print("--- Episode ", N, " ---");
        !run_interactions(bob, K);
        !run_interactions(carol, K);
        !run_interactions(dave, K);
        vesna.via.cfr_episode;
        -episode(N);
        N1 = N + 1;
        +episode(N1);
        !check_done.

+!check_done
    :   episode(N) & max_episodes(M) & N >= M
    <-  .print("\n=== TRAINING COMPLETE (", N, " episodes) ===");
        vesna.via.print_personality;
        vesna.via.print_cfr_stats;
        .stopMAS.

+!check_done
    :   episode(N)
    <-  !episode.

// Multi-interaction dispatch — runs K interactions per colleague
+!run_interactions(_, 0) <- true.

+!run_interactions(bob, K)
    :   K > 0
    <-  !bob_request;
        K1 = K - 1;
        !run_interactions(bob, K1).

+!run_interactions(carol, K)
    :   K > 0
    <-  !carol_request;
        K1 = K - 1;
        !run_interactions(carol, K1).

+!run_interactions(dave, K)
    :   K > 0
    <-  !dave_request;
        K1 = K - 1;
        !run_interactions(dave, K1).

/* ==========================================
   BOB'S REQUEST (Senior Developer)

   Pattern: Demanding but fair. Moderate reciprocity.
   Appreciates thorough work. Sometimes helps back.

   Actions and their OCEAN profiles:
   - alice_help_bob:    High A (helpful) + High C (thorough) + moderate E
   - alice_decline_bob: High C (focus on own work) + Low A
   - alice_delay_bob:   High O (flexible) + moderate A + moderate C
   ========================================== */

+!bob_request
    <-  -strategy(_); -outcome(_);
        vesna.via.set_decision_context(bob);
        .print("[BOB] Can you help me review this PR? It is complex.");
        !choose_bob_response;
        !execute_bob.

// --- Bob plan options (OCEAN-annotated, selected by Temper.select) ------

@alice_help_bob[temper([agreeableness(0.6), conscientiousness(0.4), extraversion(0.0), openness(-0.2), neuroticism(-0.4)]), effects([satisfaction(+0.1)[mood]])]
+!choose_bob_response
    :   true
    <-  +strategy(alice_help_bob).

@alice_decline_bob[temper([conscientiousness(0.6), agreeableness(-0.6), extraversion(-0.6), openness(-0.6), neuroticism(-0.8)])]
+!choose_bob_response
    :   true
    <-  +strategy(alice_decline_bob).

@alice_delay_bob[temper([openness(0.4), conscientiousness(0.4), agreeableness(-0.2), extraversion(-0.4), neuroticism(-0.8)]), effects([social_energy(-0.05)[mood]])]
+!choose_bob_response
    :   true
    <-  +strategy(alice_delay_bob).

// --- Bob outcomes ---

+!execute_bob
    :   strategy(alice_help_bob)
    <-  .print("  [Alice] 'Sure, I will review it.'");
        .random(R);
        !bob_help_result(R).

+!execute_bob
    :   strategy(alice_decline_bob)
    <-  .print("  [Alice] 'I am busy with my own work right now.'");
        .print("  [Outcome] Bob: 'Okay, I will manage.' (NEUTRAL)");
        vesna.via.record_outcome(neutral, 0.0, alice_decline_bob, bob).

+!execute_bob
    :   strategy(alice_delay_bob)
    <-  .print("  [Alice] 'I can look at it tomorrow morning.'");
        .random(R);
        !bob_delay_result(R).

+!bob_help_result(R)
    :   R < 0.35
    <-  .print("  [Outcome] PR has issues. Bob: 'Needs more work.' (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, alice_help_bob, bob).

+!bob_help_result(R)
    :   R >= 0.35
    <-  .print("  [Outcome] PR approved! Bob: 'Great review!' (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, alice_help_bob, bob).

+!bob_delay_result(R)
    :   R < 0.3
    <-  .print("  [Outcome] Bob: 'I need it sooner...' (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, alice_delay_bob, bob).

+!bob_delay_result(R)
    :   R >= 0.3
    <-  .print("  [Outcome] Bob: 'Tomorrow works, thanks.' (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, alice_delay_bob, bob).

/* ==========================================
   CAROL'S REQUEST (Junior Developer — Exploitative)

   Pattern: Asks frequently, rarely reciprocates.
   Takes credit for your help. Never helps you back.
   Over time, behavioral memory detects exploitation and then penalizes helping.

   Actions and their OCEAN profiles (plan annotations live below):
   - alice_help_carol:    High A (very helpful) + Low N (calm under pressure)
   - alice_decline_carol: High C (focus) + Low A (boundary)
   - alice_teach_carol:   High O (mentoring) + moderate C + neutral A
   ========================================== */

/* ==========================================
   DAVE'S REQUEST (Product Manager — Reciprocal)

   Pattern: Appreciative, vocal about help, always reciprocates.
   Publicly praises helpers. High social capital.
   Behavioral memory rewards helping Dave more over time.

   Actions and their OCEAN profiles:
   - alice_help_dave:    High E (social) + High A (helpful) + High O (opportunity)
   - alice_decline_dave: High C (focus) + Low E + Low A
   - alice_suggest_dave: High O (creative) + High C (efficient) + moderate A
   ========================================== */

+!dave_request
    <-  -strategy(_); -outcome(_);
        vesna.via.set_decision_context(dave);
        .print("[DAVE] 'Can you join my presentation prep? Need technical input.'");
        !choose_dave_response;
        !execute_dave.

// --- Dave plan options ---

@alice_help_dave[temper([openness(0.4), extraversion(0.2), conscientiousness(0.0), agreeableness(0.0), neuroticism(-0.8)]), effects([social_energy(+0.1)[mood], satisfaction(+0.1)[mood]])]
+!choose_dave_response
    :   true
    <-  +strategy(alice_help_dave).

@alice_decline_dave[temper([conscientiousness(0.2), agreeableness(-0.6), extraversion(-0.8), openness(-0.6), neuroticism(-0.8)])]
+!choose_dave_response
    :   true
    <-  +strategy(alice_decline_dave).

@alice_suggest_dave[temper([openness(0.4), conscientiousness(0.4), agreeableness(-0.2), extraversion(-0.4), neuroticism(-0.8)]), effects([satisfaction(+0.05)[mood]])]
+!choose_dave_response
    :   true
    <-  +strategy(alice_suggest_dave).

// --- Dave outcomes ---

+!execute_dave
    :   strategy(alice_help_dave)
    <-  .print("  [Alice] 'Sure, I will join you!'");
        .random(R);
        !dave_help_result(R).

+!execute_dave
    :   strategy(alice_decline_dave)
    <-  .print("  [Alice] 'I need to focus on my work.'");
        .print("  [Outcome] Dave: 'No problem, I understand.' (NEUTRAL)");
        vesna.via.record_outcome(neutral, 0.0, alice_decline_dave, dave).

+!execute_dave
    :   strategy(alice_suggest_dave)
    <-  .print("  [Alice] 'I cannot join, but let me suggest someone.'");
        .random(R);
        !dave_suggest_result(R).

+!dave_help_result(R)
    :   R < 0.25
    <-  .print("  [Outcome] Presentation goes poorly. (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, alice_help_dave, dave).

+!dave_help_result(R)
    :   R >= 0.25
    <-  .print("  [Outcome] Great presentation! Dave praises you publicly. (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, alice_help_dave, dave).

+!dave_suggest_result(R)
    :   R < 0.3
    <-  .print("  [Outcome] Suggestion did not work out. (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, alice_suggest_dave, dave).

+!dave_suggest_result(R)
    :   R >= 0.3
    <-  .print("  [Outcome] Dave: 'Great suggestion, thanks!' (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, alice_suggest_dave, dave).

/* ==========================================
   CAROL'S REQUEST (Junior Developer — Learning via Reciprocity)

   Pattern: Asks Alice for help. Whether she reciprocates depends on:
   - Carol's adapted reciprocity (starts 0.10, rises as Alice declines)
   - Carol's learned OCEAN personality (via CFR)

   Alice's response options (OCEAN-annotated):
   - alice_help_carol:    High A, high C (Alice helps Carol back)
   - alice_decline_carol: Low A, high C (Alice sets boundary)
   - alice_teach_carol:   High O, moderate A (Alice mentors Carol)

   Carol's outcome reward shaping (symmetric):
   - If Alice helps Carol back (alice_help_carol) → Carol gets +bonus (reciprocity recognized)
   - If Alice declines (alice_decline_carol) → Carol gets -penalty (rejection)
   - If Alice teaches (alice_teach_carol) → Carol gets neutral (growth opportunity)
   ========================================== */

+!carol_request
    <-  -strategy(_); -outcome(_);
        vesna.via.set_decision_context(carol);
        .print("[CAROL] 'I have a problem with my code. Can you help me out?'");
        !choose_alice_response_to_carol;
        !execute_alice_response_to_carol.

// --- Alice's response options to Carol (OCEAN-annotated) ---

@alice_help_carol[temper([agreeableness(0.8), conscientiousness(0.2), extraversion(0.0), openness(-0.2), neuroticism(-0.4)]), effects([satisfaction(+0.1)[mood]])]
+!choose_alice_response_to_carol
    :   true
    <-  +strategy(alice_help_carol).

@alice_decline_carol[temper([conscientiousness(0.6), agreeableness(-0.6), extraversion(-0.6), openness(-0.4), neuroticism(-0.8)])]
+!choose_alice_response_to_carol
    :   true
    <-  +strategy(alice_decline_carol).

@alice_teach_carol[temper([openness(0.6), conscientiousness(0.2), agreeableness(0.0), extraversion(-0.2), neuroticism(-0.6)]), effects([satisfaction(+0.05)[mood]])]
+!choose_alice_response_to_carol
    :   true
    <-  +strategy(alice_teach_carol).

// --- Alice's responses ---

+!execute_alice_response_to_carol
    :   strategy(alice_help_carol)
    <-  .print("  [Alice] 'Sure, let me help you fix that.'");
        .random(R);
        !alice_help_carol_result(R).

+!execute_alice_response_to_carol
    :   strategy(alice_decline_carol)
    <-  .print("  [Alice] 'I'm swamped right now. You should try to figure it out yourself.'");
        .random(R);
        !alice_decline_carol_result(R).

+!execute_alice_response_to_carol
    :   strategy(alice_teach_carol)
    <-  .print("  [Alice] 'Let's work through this together. Here's how to debug it.'");
        .random(R);
        !alice_teach_carol_result(R).

// --- Outcomes: Alice helps Carol ---

+!alice_help_carol_result(R)
    :   R < 0.4
    <-  .print("  [Outcome] Problem was harder than expected, takes time. (PARTIAL)");
        vesna.via.record_outcome(neutral, 0.0, alice_help_carol, carol);
        vesna.via.record_carol_cfr(alice_help_carol, 0.2).

+!alice_help_carol_result(R)
    :   R >= 0.4
    <-  .print("  [Outcome] Alice fixes Carol's bug. Carol: 'Thanks!' (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, alice_help_carol, carol);
        vesna.via.record_carol_cfr(alice_help_carol, 0.5).

// --- Outcomes: Alice declines Carol ---

+!alice_decline_carol_result(R)
    :   R < 0.3
    <-  .print("  [Outcome] Carol can't solve it alone, frustrated. (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, alice_decline_carol, carol);
        vesna.via.record_carol_cfr(alice_decline_carol, -0.3).

+!alice_decline_carol_result(R)
    :   R >= 0.3
    <-  .print("  [Outcome] Carol struggles but eventually figures it out. (SUCCESS - GROWTH)");
        vesna.via.record_outcome(success, 0.3, alice_decline_carol, carol);
        vesna.via.record_carol_cfr(alice_decline_carol, 0.1).

// --- Outcomes: Alice teaches Carol ---

+!alice_teach_carol_result(R)
    :   R < 0.35
    <-  .print("  [Outcome] Carol learns the debugging technique! (SUCCESS - LEARNING)");
        vesna.via.record_outcome(success, 0.5, alice_teach_carol, carol);
        vesna.via.record_carol_cfr(alice_teach_carol, 0.6).

+!alice_teach_carol_result(R)
    :   R >= 0.35
    <-  .print("  [Outcome] Carol: 'Interesting approach, but still confused.' (PARTIAL - EFFORT)");
        vesna.via.record_outcome(neutral, 0.0, alice_teach_carol, carol);
        vesna.via.record_carol_cfr(alice_teach_carol, 0.2).
