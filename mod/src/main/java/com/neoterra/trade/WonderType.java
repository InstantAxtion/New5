package com.neoterra.trade;

import net.minecraft.resources.ResourceLocation;

import java.util.Map;

import static com.minecolonies.api.research.util.ResearchConstants.*;

/** The four Grand Projects and the research effects they add per completed level. */
public enum WonderType
{
    CATHEDRAL("cathedral", Map.of(HAPPINESS, 0.03, REGENERATION, 0.1, HEALTH_BOOST, 1.0),
        "Citizens +3% happiness, +10% regeneration and +1 HP"),
    GRANDBRIDGE("grandbridge", Map.of(WALKING, 0.03),
        "Citizens walk +3% faster and Trade Couriers travel 8% faster"),
    COLOSSUS("colossus", Map.of(MELEE_DAMAGE, 0.4, ARCHER_DAMAGE, 0.4, MELEE_ARMOR, 0.04, ARCHER_ARMOR, 0.04),
        "Guards +0.4 damage and +4% armour"),
    ROYALGRANARY("royalgranary", Map.of(SATURATION, 0.04, FARMING, 0.1),
        "Meals +4% saturation, farmers +10% crops");

    public final String                        id;
    public final Map<ResourceLocation, Double> perLevel;
    public final String                        describe;

    WonderType(final String id, final Map<ResourceLocation, Double> perLevel, final String describe)
    {
        this.id = id;
        this.perLevel = perLevel;
        this.describe = describe;
    }
}
