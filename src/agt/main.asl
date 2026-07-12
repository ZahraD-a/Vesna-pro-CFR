// Alice learns which personality traits help her get along at work.
// Every episode she deals with three colleagues, and CFR nudges her OCEAN
// traits toward the responses that paid off.
//
// Bob    senior developer, demanding but fair, sometimes helps back
// Carol  junior developer, asks a lot, reciprocates once Alice sets limits
// Dave   product manager, appreciative and always reciprocates
//
// Each response plan carries an OCEAN annotation. Temper.select runs a softmax
// over those annotations to pick what Alice does. Success pays +0.5, failure
// -0.3, and behavioural memory shifts the rewards as the relationships settle.

interactions_per_colleague(10).
max_episodes(2000).

// setup

+!start
    <-  .print("Workplace help-seeking, CFR personality learning");
        .print("Alice talks to Bob (senior), Carol (junior) and Dave (PM)");
        .print("");
        vesna.via.init_behavioral_memory;
        vesna.via.print_personality;
        +episode(0);
        !episode.

// one episode: K interactions with each colleague, then a CFR update

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
    <-  .print("");
        .print("Training complete after ", N, " episodes");
        vesna.via.print_personality;
        vesna.via.print_cfr_stats;
        .stopMAS.

+!check_done
    :   episode(N)
    <-  !episode.

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

// Bob, senior developer.
// Demanding but fair. Thorough work gets approved, and he helps back now and then.

+!bob_request
    <-  -strategy(_); -outcome(_);
        vesna.via.set_decision_context(bob);
        .print("[Bob] Can you help me review this PR? It is complex.");
        !choose_bob_response;
        !execute_bob.

// Alice's options for Bob, picked by Temper.select over the OCEAN annotations

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

// Dave, product manager.
// Appreciative and vocal. Praises helpers publicly, always reciprocates.

+!dave_request
    <-  -strategy(_); -outcome(_);
        vesna.via.set_decision_context(dave);
        .print("[Dave] 'Can you join my presentation prep? Need technical input.'");
        !choose_dave_response;
        !execute_dave.

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

// Carol, junior developer.
// Asks Alice for help often. Whether she gives anything back depends on her
// adapted reciprocity (starts at 0.10, climbs as Alice keeps declining) and on
// the personality she learns through her own CFR. Carol's reward is shaped
// symmetrically: helping her back earns a bonus, declining costs a penalty,
// teaching is a neutral growth opportunity.

+!carol_request
    <-  -strategy(_); -outcome(_);
        vesna.via.set_decision_context(carol);
        .print("[Carol] 'I have a problem with my code. Can you help me out?'");
        !choose_alice_response_to_carol;
        !execute_alice_response_to_carol.

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
