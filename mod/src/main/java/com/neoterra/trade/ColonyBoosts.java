package com.neoterra.trade;

import com.google.common.reflect.TypeToken;
import com.minecolonies.api.colony.ICitizenData;
import com.minecolonies.api.colony.IColony;
import com.minecolonies.api.colony.IColonyManager;
import com.minecolonies.api.colony.buildings.IBuilding;
import com.minecolonies.api.colony.requestsystem.request.IRequest;
import com.minecolonies.api.colony.requestsystem.requestable.Stack;
import com.minecolonies.api.research.IResearchEffect;
import com.minecolonies.api.research.IResearchEffectManager;
import com.minecolonies.api.util.InventoryUtils;
import com.minecolonies.api.util.ItemStackUtils;
import com.minecolonies.core.colony.buildings.AbstractBuildingStructureBuilder;
import com.minecolonies.core.colony.buildings.utils.BuildingBuilderResource;
import com.minecolonies.core.research.GlobalResearchEffect;
import com.minecolonies.core.research.ResearchEffectManager;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static com.minecolonies.api.research.util.ResearchConstants.BLOCK_PLACE_SPEED;

/**
 * Server-side colony helpers that run every few seconds:
 * <ul>
 *   <li>builder speed and Grand Project bonuses, applied as extra strength on MineColonies' own research effects;</li>
 *   <li>up-front material requests for builders.</li>
 * </ul>
 */
public final class ColonyBoosts
{
    private int tick = 0;

    /** Marks an effect strength that includes a Neoterra bonus, and remembers the value from research alone. */
    static final class Boosted extends GlobalResearchEffect
    {
        final double base;

        Boosted(final ResourceLocation id, final double base, final double value)
        {
            super(id, "Neoterra", "", value, value);
            this.base = base;
        }
    }

    @SubscribeEvent
    public void onTick(final ServerTickEvent.Post event)
    {
        if (++tick % 100 != 0)
        {
            return;
        }
        final boolean upfront = tick % 200 == 0 && NeoterraConfig.get(NeoterraConfig.UPFRONT_MATERIALS, true);
        for (final IColony colony : IColonyManager.getInstance().getAllColonies())
        {
            try
            {
                applyBoosts(colony);
                if (upfront)
                {
                    requestUpfront(colony);
                }
            }
            catch (final RuntimeException e)
            {
                NeoterraTrade.LOG.warn("Colony {}: boost update failed", colony.getID(), e);
            }
        }
    }

    // ------------------------------------------------------------------ effects

    /** Extra effect strength this colony should get on top of its research. */
    static Map<ResourceLocation, Double> bonuses(final IColony colony)
    {
        final Map<ResourceLocation, Double> out = new HashMap<>();
        final double scale = NeoterraConfig.get(NeoterraConfig.WONDER_BONUS, 1.0);
        for (final WonderType type : WonderType.values())
        {
            final int level = BuildingWonder.level(colony, type);
            if (level > 0 && scale > 0)
            {
                type.perLevel.forEach((id, v) -> out.merge(id, v * level * scale, Double::sum));
            }
        }
        return out;
    }

    static void applyBoosts(final IColony colony)
    {
        final IResearchEffectManager effects = colony.getResearchManager().getResearchEffects();
        final Map<ResourceLocation, IResearchEffect> map = effectMap(effects);
        if (map == null)
        {
            return;
        }
        final Map<ResourceLocation, Double> bonus = bonuses(colony);
        final List<ResourceLocation> ids = new ArrayList<>(bonus.keySet());
        ids.add(BLOCK_PLACE_SPEED);
        // also revisit effects we boosted before, so a removed wonder or a config change takes the bonus away
        for (final Map.Entry<ResourceLocation, IResearchEffect> e : map.entrySet())
        {
            if (e.getValue() instanceof Boosted && !ids.contains(e.getKey()))
            {
                ids.add(e.getKey());
            }
        }
        final double speed = NeoterraConfig.get(NeoterraConfig.BUILDER_SPEED, 1.5);
        for (final ResourceLocation id : ids)
        {
            final IResearchEffect current = map.get(id);
            final double base = current instanceof Boosted b ? b.base : (current instanceof GlobalResearchEffect ? current.getEffect() : 0);
            double value;
            if (id.equals(BLOCK_PLACE_SPEED))
            {
                // MineColonies: delay *= (1 - strength). Divide the delay by the configured speed.
                value = Math.min(0.95, 1 - (1 - base) / speed);
                value += bonus.getOrDefault(id, 0.0);
            }
            else
            {
                value = base + bonus.getOrDefault(id, 0.0);
            }
            if (Math.abs(value - base) < 1e-9)
            {
                if (current instanceof Boosted)
                {
                    if (base == 0)
                    {
                        map.remove(id);
                    }
                    else
                    {
                        map.put(id, new GlobalResearchEffect(id, "", "", base, base));
                    }
                }
                continue;
            }
            if (!(current instanceof Boosted b) || Math.abs(b.getEffect() - value) > 1e-9)
            {
                map.put(id, new Boosted(id, base, value));
            }
        }
    }

    private static Field effectMapField;

    @SuppressWarnings("unchecked")
    private static Map<ResourceLocation, IResearchEffect> effectMap(final IResearchEffectManager effects)
    {
        if (!(effects instanceof ResearchEffectManager))
        {
            return null;
        }
        try
        {
            if (effectMapField == null)
            {
                effectMapField = ResearchEffectManager.class.getDeclaredField("effectMap");
                effectMapField.setAccessible(true);
            }
            return (Map<ResourceLocation, IResearchEffect>) effectMapField.get(effects);
        }
        catch (final ReflectiveOperationException e)
        {
            NeoterraTrade.LOG.error("Cannot reach MineColonies research effects", e);
            return null;
        }
    }

    // ------------------------------------------------------------------ builders

    /** Ask for every missing material of a builder's current build at once. */
    static int requestUpfront(final IColony colony)
    {
        int made = 0;
        for (final IBuilding building : colony.getServerBuildingManager().getBuildings().values())
        {
            if (!(building instanceof AbstractBuildingStructureBuilder builder) || !builder.hasWorkOrder() || !builder.getWorkOrder().isRequested())
            {
                continue;
            }
            final List<ItemStack> open = new ArrayList<>();
            for (final IRequest<? extends Stack> r : builder.getOpenRequestsOfType(-1, TypeToken.of(Stack.class)))
            {
                open.add(r.getRequest().getStack());
            }
            for (final BuildingBuilderResource res : new ArrayList<>(builder.getNeededResources().values()))
            {
                final ItemStack like = res.getItemStack();
                final int need = res.getAmount();
                if (need <= 0 || like.isEmpty() || open.stream().anyMatch(s -> ItemStackUtils.compareItemStacksIgnoreStackSize(s, like)))
                {
                    continue;
                }
                int have = InventoryUtils.hasBuildingEnoughElseCount(builder, s -> ItemStackUtils.compareItemStacksIgnoreStackSize(s, like), need);
                for (final ICitizenData worker : builder.getAllAssignedCitizen())
                {
                    have += InventoryUtils.getItemCountInItemHandler(worker.getInventory(), s -> ItemStackUtils.compareItemStacksIgnoreStackSize(s, like));
                }
                if (have >= need)
                {
                    continue;
                }
                final ItemStack wanted = like.copy();
                wanted.setCount(1);
                builder.createRequest(new Stack(wanted, need - have, 1), true);
                open.add(wanted);
                made++;
            }
        }
        return made;
    }
}
