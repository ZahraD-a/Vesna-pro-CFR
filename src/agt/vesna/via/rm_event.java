package vesna.via;

import jason.asSemantics.*;
import jason.asSyntax.*;
import vesna.RewardMachine;
import vesna.Temper;
import vesna.VesnaAgent;

import java.util.HashMap;
import java.util.Map;
import java.util.Iterator;

import static jason.asSyntax.ASSyntax.*;

/**
 * Internal action: vesna.rm_event(Event, Reward, Strategy)
 *
 * Records outcome for CFR personality learning and computes alignment reward.
 *
 * NOTE: Mood effects are applied at plan SELECTION time (via effects annotation),
 * following the original VesnaPro behavior. This action only handles CFR learning.
 *
 * <p><b>USAGE IN ASL:</b></p>
 * <pre>
 *   vesna.rm_event(success, 1.0, try_new_shop).
 *   vesna.rm_event(failure, -1.0, go_regular_shop).
 * </pre>
 *
 * @author VesnaPro CFR Extension
 */
public class rm_event extends DefaultInternalAction {

    /** Known strategy traits for alignment calculation */
    private static final Map<String, Map<String, Double>> STRATEGY_TRAITS = new HashMap<>();

    static {
        // try_new_shop: bold(0.8), curious(0.7), cautious(0.2)
        Map<String, Double> tryNewShop = new HashMap<>();
        tryNewShop.put("bold", 0.8);
        tryNewShop.put("curious", 0.7);
        tryNewShop.put("cautious", 0.2);
        STRATEGY_TRAITS.put("try_new_shop", tryNewShop);

        // go_regular_shop: cautious(0.8), bold(0.2), curious(0.3)
        Map<String, Double> goRegular = new HashMap<>();
        goRegular.put("cautious", 0.8);
        goRegular.put("bold", 0.2);
        goRegular.put("curious", 0.3);
        STRATEGY_TRAITS.put("go_regular_shop", goRegular);

        // make_at_home: cautious(0.9), curious(0.1), bold(0.1)
        Map<String, Double> makeAtHome = new HashMap<>();
        makeAtHome.put("cautious", 0.9);
        makeAtHome.put("curious", 0.1);
        makeAtHome.put("bold", 0.1);
        STRATEGY_TRAITS.put("make_at_home", makeAtHome);
    }

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {

        VesnaAgent agent = (VesnaAgent) ts.getAg();
        RewardMachine rm = agent.getRewardMachine();
        Temper temper = agent.getTemper();

        if (args.length < 2) {
            ts.getLogger().warning("[rm_event] Usage: vesna.rm_event(Event, Reward, Move)");
            return false;
        }

        // Parse event type
        String eventStr = args[0].toString().toLowerCase().trim();

        // Parse reward
        double reward = 0.0;
        if (args[1] instanceof NumberTerm) {
            reward = ((NumberTerm) args[1]).solve();
        } else {
            try {
                reward = Double.parseDouble(args[1].toString());
            } catch (NumberFormatException e) {
                if (eventStr.contains("success")) reward = 1.0;
                else if (eventStr.contains("failure")) reward = -1.0;
            }
        }

        // Get strategy: prefer explicit argument over belief base lookup
        String strategy = null;
        if (args.length >= 3) {
            strategy = args[2].toString();
        }
        if (strategy == null || strategy.equals("unknown")) {
            strategy = getStrategy(ts);
        }
        if (strategy == null || strategy.equals("unknown")) {
            ts.getLogger().warning("[rm_event] Could not determine strategy");
            return false;
        }

        ts.getLogger().info(String.format("[%s] %s: Strategy=%s, Reward=%.1f",
            "CFR", eventStr.toUpperCase(), strategy, reward));

        // Get plan traits for alignment calculation
        Map<String, Double> planTraits = STRATEGY_TRAITS.get(strategy);

        // Record to Temper for CFR
        if (temper != null) {
            temper.recordBridgeOutcome(strategy, reward);
        }

        // Record to RewardMachine with alignment
        if (rm != null) {
            rm.setTemper(temper);
            RewardMachine.Event event = reward > 0 ?
                RewardMachine.Event.SUCCESS : (reward < 0 ? RewardMachine.Event.FAILURE : RewardMachine.Event.SUCCESS);
            rm.computeReward(event, strategy, planTraits);
        }

        return true;
    }

    private String getStrategy(TransitionSystem ts) {
        try {
            Literal strategyPattern = createLiteral("strategy", new VarTerm("X"));
            Iterator<Literal> it = ts.getAg().getBB().getCandidateBeliefs(strategyPattern, null);
            if (it != null && it.hasNext()) {
                Literal strategy = it.next();
                return strategy.getTerm(0).toString();
            }
        } catch (Exception e) {
            // Ignore
        }
        return "unknown";
    }
}
