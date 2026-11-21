package com.neoterra.trade;

import net.minecraft.resources.ResourceLocation;

import java.util.Map;

import static com.minecolonies.api.research.util.ResearchConstants.*;

/** The Grand Projects and the research effects they add per completed level. */
public enum WonderType
{
    CATHEDRAL("cathedral", Map.of(HAPPINESS, 0.03, REGENERATION, 0.1, HEALTH_BOOST, 1.0),
        "Citizens +3% happiness, +10% regeneration and +1 HP"),
    GRANDBRIDGE("grandbridge", Map.of(WALKING, 0.03),
        "Citizens walk +3% faster and Trade Couriers travel 8% faster"),
    COLOSSUS("colossus", Map.of(MELEE_DAMAGE, 0.4, ARCHER_DAMAGE, 0.4, MELEE_ARMOR, 0.04, ARCHER_ARMOR, 0.04),
        "Guards +0.4 damage and +4% armour"),
    ROYALGRANARY("royalgranary", Map.of(SATURATION, 0.05),
        "Meals +5% saturation"),
    GREATLIBRARY("greatlibrary", Map.of(LEVELING, 0.04, TEACHING, 0.04),
        "Citizens gain skill +4% faster, pupils learn +4% faster"),
    HANGINGGARDENS("hanginggardens", Map.of(GROWTH, 0.04, FARMING, 0.04),
        "Children grow up +4% faster, farmers harvest +4% more"),
    GREATFORGE("greatforge", Map.of(BLOCK_BREAK_SPEED, 0.04, TOOL_DURABILITY, 0.03, MORE_ORES, 0.03),
        "Workers break blocks +4% faster, tools last +3% longer, miners find +3% more ores");

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
