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
import com.minecolonies.core.colony.jobs.AbstractJobCrafter;
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


/**
 * Server-side colony helpers that run every few seconds:
 * <ul>
 *   <li>Grand Project bonuses, applied as extra strength on MineColonies' own research effects;</li>
 *   <li>the University's workshop research: crafters finish each craft a little sooner;</li>
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

    /** Research effect of the University line "Efficient Benches / Workshop Rhythm / Master Artisans". */
    public static final ResourceLocation CRAFTING_SPEED = NeoterraTrade.id("effects/craftingspeed");

    /** Fractional extra crafting progress per crafter (colony id << 32 | citizen id). */
    private final Map<Long, Double> craftCarry = new HashMap<>();

    @SubscribeEvent
    public void onTick(final ServerTickEvent.Post event)
    {
        ++tick;
        if (tick % 10 == 0)
        {
            for (final IColony colony : IColonyManager.getInstance().getAllColonies())
            {
                speedUpCrafters(colony, craftCarry);
            }
        }
        if (tick % 100 != 0)
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
        // also revisit effects we boosted before, so a removed wonder or a config change takes the bonus away
        for (final Map.Entry<ResourceLocation, IResearchEffect> e : map.entrySet())
        {
            if (e.getValue() instanceof Boosted && !ids.contains(e.getKey()))
            {
                ids.add(e.getKey());
            }
        }
        for (final ResourceLocation id : ids)
        {
            final IResearchEffect current = map.get(id);
            final double base = current instanceof Boosted b ? b.base : (current instanceof GlobalResearchEffect ? current.getEffect() : 0);
            final double value = base + bonus.getOrDefault(id, 0.0);
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

    // ------------------------------------------------------------------ crafters

    /**
     * Crafters gain one point of progress per hit (every 10 ticks) while they work on a recipe; with the
     * research at strength s they get s extra points per 10 ticks, i.e. each craft finishes ~s faster.
     * Returns the number of crafters that were sped up.
     */
    static int speedUpCrafters(final IColony colony, final Map<Long, Double> carry)
    {
        final double strength = colony.getResearchManager().getResearchEffects().getEffectStrength(CRAFTING_SPEED);
        if (strength <= 0)
        {
            return 0;
        }
        int n = 0;
        for (final ICitizenData citizen : colony.getCitizenManager().getCitizens())
        {
            if (!(citizen.getJob() instanceof AbstractJobCrafter<?, ?> job) || job.getCurrentTask() == null || job.getProgress() <= 0)
            {
                continue;
            }
            final long key = ((long) colony.getID() << 32) | (citizen.getId() & 0xffffffffL);
            double c = carry.getOrDefault(key, 0.0) + strength;
            if (c >= 1)
            {
                job.setProgress(job.getProgress() + (int) c);
                c -= (int) c;
            }
            carry.put(key, c);
            n++;
        }
        return n;
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
