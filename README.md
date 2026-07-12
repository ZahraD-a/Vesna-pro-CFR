# VesnaPro CFR

VesnaPro builds BDI agents in Jason where each agent carries a set of
propensities, its Temper, split into an immutable Personality and a mutable
Mood. Plans are annotated with propensities and effects, and among the
applicable plans the agent selects one based on how well the plan matches its
temper.

This fork adds Counterfactual Regret Minimization so the personality is no
longer fixed at design time. The agent accumulates regret over repeated
decisions per context and shifts its personality toward the propensities that
experience favoured. Plan selection keeps working unchanged on the evolved
temper.

## Scenario

`src/agt/main.asl` runs a workplace scenario. Alice deals with three colleagues
over many episodes:

- Bob, a senior developer, demanding but fair
- Carol, a junior developer who reciprocates once Alice sets limits
- Dave, a product manager who always reciprocates

Each of Alice's response plans is OCEAN-annotated. CFR nudges her traits toward
the responses that paid off, and Carol learns her own traits the same way.

## Configuration

Assign a temper to an agent in `vesna.jcm`:

    agent alice:main.asl {
        ag-class:     vesna.VesnaAgent
        temper:       temper( openness(0.0), conscientiousness(0.0), extraversion(0.0), agreeableness(0.0), neuroticism(0.0), stress(0.0)[mood], satisfaction(0.0)[mood], social_energy(0.0)[mood] )
        strategy:     random
        seed:         0
        cfr_learning: true
        goals:        start
    }

- `ag-class` gives the agent the Vesna choice-management class.
- `temper` sets the propensities. Those tagged `[mood]` are mutable.
- `strategy` is the plan-selection strategy (`nearest` or `most_similar`).
- `cfr_learning` turns on regret-based personality updates.

## Plan annotation

Add the temper and effects to the plan label:

    @alice_help_bob[ temper( [ agreeableness( 0.6 ), conscientiousness( 0.4 ) ] ), effects( [ satisfaction( 0.1 )[mood] ] ) ]
    +!choose_bob_response
        :   true
        <-  +strategy( alice_help_bob ).

The plan carries its own temper and a set of effects that update the agent's
mood when it runs.

## Running

From the directory that holds `build.gradle`:

    gradle run

The run is headless, so no virtual body is needed. Tweak the temper, strategy
or seed in `vesna.jcm` and run again to see the behaviour change.

## References

- Vesna-Pro, the framework this builds on: https://github.com/VEsNA-ToolKit/vesna-pro
- Counterfactual Regret Minimization: https://modelai.gettysburg.edu/2013/cfr/cfr.pdf
