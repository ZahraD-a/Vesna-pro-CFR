# VesnaPro

**Vesna** is a framework for building embodied agents using [Jason](https://github.com/jason-lang/jason) and [Godot](https://godotengine.org/).
**VesnaPro** extends Vesna by allowing developers to build agents with **propensities**.

Each agent possesses a set of propensities, collectively known as its _Temper_, which is subdivided into:
- **Personality**: Immutable propensities;
- **Mood**: Mutable propensities.

In VesnaPro, plans are annotated with propensities and effects. Among the applicable plans, agents select one based on their temper.

There are two strategies for plan selection:
- **Nearest**: Selects the plan with the temper closest to the agent's temper (deterministic);
- **Most Similar**: Selects a plan based on random weights derived from similarity metrics (probabilistic).

## Configuration

To assign a temper to an agent, modify the `.jcm` file as follows:

```jason
    agent alice:alice.asl {
        ag-class:   vesna.VesnaAgent
        temper:     temper( prop1(0.2), prop2(0.3), prop3(-0.5)[mood], prop4(0.3)[mood] )
        strategy:   most_similar
        address:    localhost
        port:       9080
    }
```

- `ag-class`: The `vesna.VesnaAgent` class implements core Vesna features and choice management.
- `temper`: Defines the agent's propensities. Note that propensities tagged with `[mood]` are mutable.
- `strategy`: Sets the selection strategy. Options are `nearest` or `most_similar`.

## Plan Annotation

To annotate a plan, add the annotation to the plan label:

```jason
@p1[ temper( [ prop1( 0.0 ), prop2( 0.3 ) ] ), effects( [ prop3( 0.7 ), prop4( -0.05 ) ] ) ]
+!p
    :   true
    <-  .print( "ciao" ).
```

In this example, the plan `!p` has its own temper and a set of effects. These effects will modify the agent's mood upon execution.

## Running the Example

To run the example, follow these steps:

1.  **Start the Environment**: Ensure a WebSocket server is listening on `localhost:9080`. This will acts as the agent's body (or a placeholder) to prevent connection errors.
2.  **Launch the Agent**: Execute the project from the directory containing `build.gradle` using:
    ```bash
    gradle run
    ```
3.  **Experiment**: Watch the agent in action, tweak the configuration, and have fun!

For integration with a full virtual environment, refer to the Vesna documentation. Ensure your virtual body is accessible at `localhost:9080`.