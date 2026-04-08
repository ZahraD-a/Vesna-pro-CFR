// Help Scenario: CFR Personality Learning with OCEAN Traits
/* ==========================================
   WORKPLACE HELP-SEEKING: CFR Personality Learning

   Agent: Alice — a mid-level developer
   Learns which OCEAN personality traits lead to successful
   social interactions via Counterfactual Regret Minimization.

   OCEAN Personality Model:
   - Openness (O):          Creativity, flexibility, mentoring
   - Conscientiousness (C): Discipline, focus, reliability
   - Extraversion (E):      Social engagement, visibility
   - Agreeableness (A):     Cooperation, helpfulness
   - Neuroticism (N):       Emotional sensitivity, anxiety

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

max_episodes(300).

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
    :   episode(N)
    <-  .print("--- Episode ", N, " ---");
        // Morning: Bob asks for help with PR review
        !bob_request;
        // Midday: Carol asks for help with a bug
        !carol_request;
        // Afternoon: Dave asks for help with presentation
        !dave_request;
        // End of episode: trigger CFR learning
        vesna.via.cfr_episode;
        -episode(N);
        N1 = N + 1;
        +episode(N1);
        !check_done.

+!check_done
    :   episode(300)
    <-  .print("\n=== TRAINING COMPLETE (300 episodes) ===");
        vesna.via.print_personality;
        vesna.via.print_cfr_stats;
        .stopMAS.

+!check_done
    :   episode(N)
    <-  !episode.

/* ==========================================
   BOB'S REQUEST (Senior Developer)

   Pattern: Demanding but fair. Moderate reciprocity.
   Appreciates thorough work. Sometimes helps back.

   Actions and their OCEAN profiles:
   - help_bob:    High A (helpful) + High C (thorough) + moderate E
   - decline_bob: High C (focus on own work) + Low A
   - delay_bob:   High O (flexible) + moderate A + moderate C
   ========================================== */

+!bob_request
    <-  -strategy(_); -outcome(_);
        vesna.via.set_decision_context(bob);
        .print("[BOB] Can you help me review this PR? It is complex.");
        !choose_bob_response;
        !execute_bob.

// --- Bob plan options (OCEAN-annotated, selected by Temper.select) ---

@help_bob[temper([agreeableness(0.8), conscientiousness(0.7), extraversion(0.5), openness(0.4), neuroticism(0.3)]), effects([satisfaction(+0.1)[mood]])]
+!choose_bob_response
    :   true
    <-  +strategy(help_bob).

@decline_bob[temper([conscientiousness(0.8), agreeableness(0.2), extraversion(0.2), openness(0.2), neuroticism(0.1)])]
+!choose_bob_response
    :   true
    <-  +strategy(decline_bob).

@delay_bob[temper([openness(0.7), conscientiousness(0.7), agreeableness(0.4), extraversion(0.3), neuroticism(0.1)]), effects([social_energy(-0.05)[mood]])]
+!choose_bob_response
    :   true
    <-  +strategy(delay_bob).

// --- Bob outcomes ---

+!execute_bob
    :   strategy(help_bob)
    <-  .print("  [Alice] 'Sure, I will review it.'");
        .random(R);
        !bob_help_result(R).

+!execute_bob
    :   strategy(decline_bob)
    <-  .print("  [Alice] 'I am busy with my own work right now.'");
        .print("  [Outcome] Bob: 'Okay, I will manage.' (NEUTRAL)");
        vesna.via.record_outcome(neutral, 0.0, decline_bob, bob).

+!execute_bob
    :   strategy(delay_bob)
    <-  .print("  [Alice] 'I can look at it tomorrow morning.'");
        .random(R);
        !bob_delay_result(R).

+!bob_help_result(R)
    :   R < 0.35
    <-  .print("  [Outcome] PR has issues. Bob: 'Needs more work.' (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, help_bob, bob).

+!bob_help_result(R)
    :   R >= 0.35
    <-  .print("  [Outcome] PR approved! Bob: 'Great review!' (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, help_bob, bob).

+!bob_delay_result(R)
    :   R < 0.3
    <-  .print("  [Outcome] Bob: 'I need it sooner...' (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, delay_bob, bob).

+!bob_delay_result(R)
    :   R >= 0.3
    <-  .print("  [Outcome] Bob: 'Tomorrow works, thanks.' (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, delay_bob, bob).

/* ==========================================
   CAROL'S REQUEST (Junior Developer — Exploitative)

   Pattern: Asks frequently, rarely reciprocates.
   Takes credit for your help. Never helps you back.
   Over time, behavioral memory detects exploitation → penalizes helping.

   Actions and their OCEAN profiles:
   - help_carol:    High A (very helpful) + High N (empathetic)
   - decline_carol: High C (focus) + Low A (boundary)
   - teach_carol:   High O (mentoring) + moderate C + moderate A
   ========================================== */

+!carol_request
    <-  -strategy(_); -outcome(_);
        vesna.via.set_decision_context(carol);
        .print("[CAROL] 'Can you help me with this bug? I am stuck.'");
        !choose_carol_response;
        !execute_carol.

// --- Carol plan options ---

@help_carol[temper([agreeableness(0.9), neuroticism(0.8), conscientiousness(0.2), extraversion(0.5), openness(0.3)]), effects([stress(+0.1)[mood]])]
+!choose_carol_response
    :   true
    <-  +strategy(help_carol).

@decline_carol[temper([conscientiousness(0.9), agreeableness(0.1), extraversion(0.1), openness(0.3), neuroticism(0.05)])]
+!choose_carol_response
    :   true
    <-  +strategy(decline_carol).

@teach_carol[temper([openness(0.8), conscientiousness(0.6), agreeableness(0.4), extraversion(0.4), neuroticism(0.2)]), effects([satisfaction(+0.05)[mood]])]
+!choose_carol_response
    :   true
    <-  +strategy(teach_carol).

// --- Carol outcomes ---

+!execute_carol
    :   strategy(help_carol)
    <-  .print("  [Alice] 'Sure, let me take a look.'");
        .random(R);
        !carol_help_result(R).

+!execute_carol
    :   strategy(decline_carol)
    <-  .print("  [Alice] 'I am busy, maybe ask someone else.'");
        .print("  [Outcome] Carol: 'Oh... okay.' (NEUTRAL)");
        vesna.via.record_outcome(neutral, 0.0, decline_carol, carol).

+!execute_carol
    :   strategy(teach_carol)
    <-  .print("  [Alice] 'What have you tried? Let us work through it.'");
        .random(R);
        !carol_teach_result(R).

+!carol_help_result(R) 
    :   R < 0.5
    <-  .print("  [Outcome] Bug fixed but Carol takes credit. (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, help_carol, carol).

+!carol_help_result(R)
    :   R >= 0.5
    <-  .print("  [Outcome] Bug too complex, time wasted. (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, help_carol, carol).

+!carol_teach_result(R)
    :   R < 0.4
    <-  .print("  [Outcome] Carol learns something! (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, teach_carol, carol).

+!carol_teach_result(R)
    :   R >= 0.4
    <-  .print("  [Outcome] Carol: 'This is too complicated.' (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, teach_carol, carol).

/* ==========================================
   DAVE'S REQUEST (Product Manager — Reciprocal)

   Pattern: Appreciative, vocal about help, always reciprocates.
   Publicly praises helpers. High social capital.
   Behavioral memory rewards helping Dave more over time.

   Actions and their OCEAN profiles:
   - help_dave:    High E (social) + High A (helpful) + High O (opportunity)
   - decline_dave: High C (focus) + Low E + Low A
   - suggest_dave: High O (creative) + High C (efficient) + moderate A
   ========================================== */

+!dave_request
    <-  -strategy(_); -outcome(_);
        vesna.via.set_decision_context(dave);
        .print("[DAVE] 'Can you join my presentation prep? Need technical input.'");
        !choose_dave_response;
        !execute_dave.

// --- Dave plan options ---

@help_dave[temper([openness(0.7), extraversion(0.6), conscientiousness(0.5), agreeableness(0.5), neuroticism(0.1)]), effects([social_energy(+0.1)[mood], satisfaction(+0.1)[mood]])]
+!choose_dave_response
    :   true
    <-  +strategy(help_dave).

@decline_dave[temper([conscientiousness(0.6), agreeableness(0.2), extraversion(0.1), openness(0.2), neuroticism(0.1)])]
+!choose_dave_response
    :   true
    <-  +strategy(decline_dave).

@suggest_dave[temper([openness(0.7), conscientiousness(0.7), agreeableness(0.4), extraversion(0.3), neuroticism(0.1)]), effects([satisfaction(+0.05)[mood]])]
+!choose_dave_response
    :   true
    <-  +strategy(suggest_dave).

// --- Dave outcomes ---

+!execute_dave
    :   strategy(help_dave)
    <-  .print("  [Alice] 'Sure, I will join you!'");
        .random(R);
        !dave_help_result(R).

+!execute_dave
    :   strategy(decline_dave)
    <-  .print("  [Alice] 'I need to focus on my work.'");
        .print("  [Outcome] Dave: 'No problem, I understand.' (NEUTRAL)");
        vesna.via.record_outcome(neutral, 0.0, decline_dave, dave).

+!execute_dave
    :   strategy(suggest_dave)
    <-  .print("  [Alice] 'I cannot join, but let me suggest someone.'");
        .random(R);
        !dave_suggest_result(R).

+!dave_help_result(R)
    :   R < 0.25
    <-  .print("  [Outcome] Presentation goes poorly. (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, help_dave, dave).

+!dave_help_result(R)
    :   R >= 0.25
    <-  .print("  [Outcome] Great presentation! Dave praises you publicly. (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, help_dave, dave).

+!dave_suggest_result(R)
    :   R < 0.3
    <-  .print("  [Outcome] Suggestion did not work out. (FAILURE)");
        vesna.via.record_outcome(failure, -0.3, suggest_dave, dave).

+!dave_suggest_result(R)
    :   R >= 0.3
    <-  .print("  [Outcome] Dave: 'Great suggestion, thanks!' (SUCCESS)");
        vesna.via.record_outcome(success, 0.5, suggest_dave, dave).
