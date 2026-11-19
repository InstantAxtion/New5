package com.neoterra.trade;

import com.minecolonies.api.colony.IColony;
import com.minecolonies.api.colony.buildings.IBuilding;
import com.minecolonies.core.colony.buildings.AbstractBuilding;
import net.minecraft.core.BlockPos;
import org.jetbrains.annotations.NotNull;

/**
 * A Grand Project. Its blueprint holds wing child huts (built and upgraded by other builders at the
 * same time); the colony bonus counts the lowest level of the core and all its wings.
 */
public class BuildingWonder extends AbstractBuilding
{
    private final WonderType type;

    public BuildingWonder(final IColony colony, final BlockPos pos, final WonderType type)
    {
        super(colony, pos);
        this.type = type;
    }

    public WonderType getType()
    {
        return type;
    }

    @NotNull
    @Override
    public String getSchematicName()
    {
        return type.id;
    }

    @Override
    public int getMaxBuildingLevel()
    {
        return 5;
    }

    /** Completed level: the core and every wing have reached it. */
    public int bonusLevel()
    {
        int level = getBuildingLevel();
        for (final BlockPos child : getChildren())
        {
            final IBuilding wing = getColony().getServerBuildingManager().getBuilding(child);
            if (wing != null)
            {
                level = Math.min(level, wing.getBuildingLevel());
            }
        }
        return Math.max(0, level);
    }

    /** Highest completed level of a wonder type in a colony (0 if none). */
    public static int level(final IColony colony, final WonderType type)
    {
        int best = 0;
        for (final IBuilding b : colony.getServerBuildingManager().getBuildings().values())
        {
            if (b instanceof BuildingWonder w && w.type == type)
            {
                best = Math.max(best, w.bonusLevel());
            }
        }
        return best;
    }

    /** A wing of a Grand Project – a separate child hut so a second (third, ...) builder can work on it. */
    public static class Wing extends AbstractBuilding
    {
        public Wing(final IColony colony, final BlockPos pos)
        {
            super(colony, pos);
        }

        @NotNull
        @Override
        public String getSchematicName()
        {
            return "wonderwing";
        }

        @Override
        public int getMaxBuildingLevel()
        {
            return 5;
        }
    }
}
