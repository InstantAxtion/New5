package com.neoterra.trade;

import net.neoforged.neoforge.common.ModConfigSpec;

/** Server config: config/neoterra-server.toml (per world in serverconfig/). */
public final class NeoterraConfig
{
    public static final ModConfigSpec SPEC;

    public static final ModConfigSpec.DoubleValue  BUILDER_SPEED;
    public static final ModConfigSpec.BooleanValue UPFRONT_MATERIALS;
    public static final ModConfigSpec.BooleanValue SUPPLY_DEPOT;
    public static final ModConfigSpec.DoubleValue  WONDER_BONUS;
    public static final ModConfigSpec.BooleanValue TRADE_POST;

    static
    {
        final ModConfigSpec.Builder b = new ModConfigSpec.Builder();
        b.push("builders");
        BUILDER_SPEED = b.comment("How fast builders place blocks. 1.0 = normal MineColonies speed, 2.0 = twice as fast, 0.5 = half speed.",
            "Stacks with the builder speed research.").defineInRange("builderSpeed", 1.5, 0.25, 10.0);
        UPFRONT_MATERIALS = b.comment("When a builder has worked out the material list of a build, request everything still missing at once",
            "instead of one stage at a time, so the warehouse and crafters can work on all of it in parallel.").define("upfrontMaterials", true);
        b.pop();
        b.push("huts");
        SUPPLY_DEPOT = b.comment("Supply Depot: its Quartermaster crafts requested items nobody else in the colony makes.").define("supplyDepot", true);
        TRADE_POST = b.comment("Trade Post: pass requests a colony cannot fulfil to the linked colony.").define("tradePost", true);
        b.pop();
        b.push("wonders");
        WONDER_BONUS = b.comment("Strength of Grand Project (wonder) bonuses. 1.0 = default, 0 = off, 2.0 = double.").defineInRange("wonderBonus", 1.0, 0.0, 5.0);
        b.pop();
        SPEC = b.build();
    }

    private NeoterraConfig() {}

    static double get(final ModConfigSpec.DoubleValue v, final double fallback)
    {
        return SPEC.isLoaded() ? v.get() : fallback;
    }

    static boolean get(final ModConfigSpec.BooleanValue v, final boolean fallback)
    {
        return SPEC.isLoaded() ? v.get() : fallback;
    }
}
