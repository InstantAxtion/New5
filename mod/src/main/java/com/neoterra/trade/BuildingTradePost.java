package com.neoterra.trade;

import com.minecolonies.api.colony.IColony;
import com.minecolonies.api.colony.IColonyManager;
import com.minecolonies.api.colony.buildings.IBuilding;
import com.minecolonies.api.colony.requestsystem.request.IRequest;
import com.minecolonies.api.colony.requestsystem.request.RequestState;
import com.minecolonies.api.colony.requestsystem.requestable.Stack;
import com.minecolonies.api.colony.requestsystem.token.IToken;
import com.minecolonies.api.colony.requestsystem.token.StandardToken;
import net.minecraft.util.Tuple;
import com.minecolonies.core.colony.buildings.AbstractBuilding;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemHandlerHelper;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.function.Predicate;
import java.util.Set;
import java.util.UUID;

/**
 * The Trade Post. Two posts in different colonies are linked with a Trade Ledger.
 * <p>
 * Importing side: requests in its colony that nobody can resolve (they end up with the player)
 * are copied as requests of the partner post in the partner colony, where builders, stonemasons,
 * the warehouse etc. fulfil them and deliver into the partner post.
 * <p>
 * Exporting side: its Trade Courier collects those goods from the post and carries them over.
 * On arrival the goods are put into the building that asked for them and the original request
 * is closed.
 */
public class BuildingTradePost extends AbstractBuilding
{
    public static final String SCHEMATIC = "tradepost";

    public static final int MODE_BOTH   = 0;
    public static final int MODE_EXPORT = 1;
    public static final int MODE_IMPORT = 2;

    /** Partner post. */
    private int                partnerColony = -1;
    private ResourceKey<Level> partnerDim    = Level.OVERWORLD;
    private BlockPos           partnerPos    = BlockPos.ZERO;
    private int                mode          = MODE_BOTH;

    /** Importing side: original request tokens that were copied to the partner. */
    private final Set<UUID> mirrored = new HashSet<>();

    /** Exporting side: goods the partner asked for. */
    private final List<Order> orders = new ArrayList<>();

    /** Exporting side: goods on the road. */
    private final List<Shipment> transit = new ArrayList<>();

    private int tickCounter = 0;

    public BuildingTradePost(final IColony colony, final BlockPos pos)
    {
        super(colony, pos);
    }

    @NotNull
    @Override
    public String getSchematicName()
    {
        return SCHEMATIC;
    }

    @Override
    public int getMaxBuildingLevel()
    {
        return 5;
    }

    // ------------------------------------------------------------------ link

    public boolean isLinked()
    {
        return partnerColony >= 0;
    }

    public void link(final IColony other, final BlockPos otherPos)
    {
        partnerColony = other.getID();
        partnerDim = other.getDimension();
        partnerPos = otherPos.immutable();
        mirrored.clear();
        markDirty();
    }

    public void unlink()
    {
        partnerColony = -1;
        mirrored.clear();
        orders.clear();
        markDirty();
    }

    public int getMode()
    {
        return mode;
    }

    public int cycleMode()
    {
        mode = (mode + 1) % 3;
        markDirty();
        return mode;
    }

    public boolean canExport()
    {
        return mode != MODE_IMPORT;
    }

    public boolean canImport()
    {
        return mode != MODE_EXPORT;
    }

    public int getPartnerColony()
    {
        return partnerColony;
    }

    public BlockPos getPartnerPos()
    {
        return partnerPos;
    }

    /** The partner post, if its colony and building still exist. */
    @Nullable
    public BuildingTradePost getPartner()
    {
        if (!isLinked())
        {
            return null;
        }
        final IColony other = IColonyManager.getInstance().getColonyByDimension(partnerColony, partnerDim);
        if (other == null)
        {
            return null;
        }
        final IBuilding b = other.getServerBuildingManager().getBuilding(partnerPos);
        if (b instanceof BuildingTradePost post && post.isLinked() && post.partnerColony == getColony().getID() && post.partnerPos.equals(getPosition()))
        {
            return post;
        }
        return null;
    }

    /** How many orders may be open at once. */
    private int capacity()
    {
        return Math.max(1, getBuildingLevel()) * 4;
    }

    // ------------------------------------------------------------------ ticking

    @Override
    public void onColonyTick(@NotNull final IColony colony)
    {
        super.onColonyTick(colony);
        if (getBuildingLevel() <= 0 || ++tickCounter % 5 != 0)
        {
            return;
        }
        final BuildingTradePost partner = getPartner();
        if (partner != null && partner.getBuildingLevel() > 0 && canImport() && partner.canExport())
        {
            mirrorRequests(partner);
        }
        deliverArrivals();
    }

    /** Importing side: copy stuck requests of this colony to the partner. */
    private void mirrorRequests(final BuildingTradePost partner)
    {
        final IColony colony = getColony();
        // requests nobody in this colony can fulfil: waiting for a retry, or handed to the player
        final List<IToken<?>> stuck = new ArrayList<>(colony.getRequestManager().getPlayerResolver().getAllAssignedRequests());
        stuck.addAll(colony.getRequestManager().getRetryingRequestResolver().getAllAssignedRequests());
        final Set<UUID> open = new HashSet<>();
        for (final IToken<?> token : stuck)
        {
            final IRequest<?> request;
            try
            {
                request = colony.getRequestManager().getRequestForToken(token);
            }
            catch (final IllegalArgumentException e)
            {
                continue;
            }
            if (request == null || !(request.getRequest() instanceof Stack stack) || !(token.getIdentifier() instanceof UUID uuid))
            {
                continue;
            }
            // never relay requests made by trade posts – that would bounce goods back and forth
            final BlockPos where = request.getRequester().getLocation().getInDimensionLocation();
            if (colony.getServerBuildingManager().getBuilding(where) instanceof BuildingTradePost)
            {
                continue;
            }
            open.add(uuid);
            if (mirrored.contains(uuid) || partner.orders.size() >= partner.capacity())
            {
                continue;
            }
            final ItemStack wanted = stack.getStack().copy();
            final int count = Math.max(1, stack.getCount());
            wanted.setCount(1);
            partner.addOrder(new Order(uuid, colony.getID(), colony.getDimension(), getPosition(), wanted, count));
            mirrored.add(uuid);
            markDirty();
        }
        // forget requests that were resolved some other way
        if (mirrored.retainAll(open))
        {
            markDirty();
        }
    }

    /** Exporting side: a new order from the partner, requested in this colony. */
    private void addOrder(final Order order)
    {
        orders.add(order);
        createRequest(new Stack(order.stack.copy(), order.count, order.count), true);
        markDirty();
    }

    /** Exporting side: is there an order whose goods are all waiting in the post? */
    @Nullable
    public Order nextReadyOrder()
    {
        final IItemHandler handler = getItemHandlerCap();
        if (handler == null)
        {
            return null;
        }
        for (final Order order : orders)
        {
            if (count(handler, order.stack) >= order.count)
            {
                return order;
            }
        }
        return null;
    }

    /** Exporting side: take the goods of an order out of the post and put them on the road. */
    public boolean dispatch(final Order order, final int travelTicks)
    {
        final IItemHandler handler = getItemHandlerCap();
        if (handler == null || count(handler, order.stack) < order.count || !orders.remove(order))
        {
            return false;
        }
        final List<ItemStack> cargo = new ArrayList<>();
        int left = order.count;
        for (int slot = 0; slot < handler.getSlots() && left > 0; slot++)
        {
            if (ItemStack.isSameItemSameComponents(handler.getStackInSlot(slot), order.stack))
            {
                final ItemStack got = handler.extractItem(slot, left, false);
                left -= got.getCount();
                if (!got.isEmpty())
                {
                    cargo.add(got);
                }
            }
        }
        transit.add(new Shipment(order, cargo, getColony().getWorld().getGameTime() + travelTicks));
        markDirty();
        return true;
    }

    /** Travel time to the partner, shorter with a better courier hut. */
    public int travelTicks()
    {
        final double dist = getPartnerDim().equals(getColony().getDimension()) ? Math.sqrt(getPosition().distSqr(partnerPos)) : 3000;
        final double ticks = Math.min(12000, Math.max(400, dist * 1.5));
        return (int) (ticks * (1.0 - 0.1 * (Math.max(1, getBuildingLevel()) - 1)));
    }

    public ResourceKey<Level> getPartnerDim()
    {
        return partnerDim;
    }

    /** Exporting side: hand over everything that has arrived. */
    private void deliverArrivals()
    {
        final long now = getColony().getWorld().getGameTime();
        boolean changed = false;
        for (final Iterator<Shipment> it = transit.iterator(); it.hasNext(); )
        {
            final Shipment s = it.next();
            if (s.arrival <= now && deliver(s))
            {
                it.remove();
                changed = true;
            }
        }
        if (changed)
        {
            markDirty();
        }
    }

    /** Put a shipment into the building that wanted it and close the original request. */
    private boolean deliver(final Shipment s)
    {
        final IColony target = IColonyManager.getInstance().getColonyByDimension(s.order.colony, s.order.dim);
        if (target == null)
        {
            return false;
        }
        IBuilding destination = target.getServerBuildingManager().getBuilding(s.order.post);
        IToken<?> token = new StandardToken(s.order.token);
        IRequest<?> request = null;
        try
        {
            request = target.getRequestManager().getRequestForToken(token);
        }
        catch (final IllegalArgumentException ignored)
        {
            // request is gone
        }
        final boolean open = request != null && request.getState() != RequestState.COMPLETED && request.getState() != RequestState.CANCELLED
                               && request.getState() != RequestState.OVERRULED && request.getState() != RequestState.RECEIVED;
        if (open)
        {
            final IBuilding requester = target.getServerBuildingManager().getBuilding(request.getRequester().getLocation().getInDimensionLocation());
            if (requester != null)
            {
                destination = requester;
            }
        }
        if (destination == null)
        {
            return false;
        }
        final IItemHandler handler = destination.getItemHandlerCap();
        if (handler == null)
        {
            return false;
        }
        ItemStack first = ItemStack.EMPTY;
        for (final ItemStack stack : s.cargo)
        {
            if (first.isEmpty())
            {
                first = stack.copy();
            }
            final ItemStack rest = ItemHandlerHelper.insertItemStacked(handler, stack.copy(), false);
            if (!rest.isEmpty() && target.getWorld() != null)
            {
                // full: drop it at the door instead of losing it
                final BlockPos p = destination.getPosition().above();
                net.minecraft.world.Containers.dropItemStack(target.getWorld(), p.getX() + 0.5, p.getY(), p.getZ() + 0.5, rest);
            }
        }
        if (open)
        {
            first.setCount(s.order.count);
            target.getRequestManager().overruleRequest(token, first);
        }
        final IBuilding home = target.getServerBuildingManager().getBuilding(s.order.post);
        if (home instanceof BuildingTradePost post)
        {
            post.mirrored.remove(s.order.token);
            post.markDirty();
        }
        return true;
    }

    private static int count(final IItemHandler handler, final ItemStack like)
    {
        int n = 0;
        for (int slot = 0; slot < handler.getSlots(); slot++)
        {
            final ItemStack s = handler.getStackInSlot(slot);
            if (ItemStack.isSameItemSameComponents(s, like))
            {
                n += s.getCount();
            }
        }
        return n;
    }

    /** Keep the goods of open orders in the post: the colony's couriers must not haul them back to the warehouse. */
    @Override
    public Map<Predicate<ItemStack>, Tuple<Integer, Boolean>> getRequiredItemsAndAmount()
    {
        final Map<Predicate<ItemStack>, Tuple<Integer, Boolean>> keep = super.getRequiredItemsAndAmount();
        for (final Order order : orders)
        {
            final ItemStack like = order.stack;
            keep.put(stack -> ItemStack.isSameItemSameComponents(stack, like), new Tuple<>(order.count, false));
        }
        return keep;
    }

    public int openOrders()
    {
        return orders.size();
    }

    public int inTransit()
    {
        return transit.size();
    }

    // ------------------------------------------------------------------ saving

    @Override
    public CompoundTag serializeNBT(@NotNull final HolderLookup.Provider provider)
    {
        final CompoundTag tag = super.serializeNBT(provider);
        final CompoundTag trade = new CompoundTag();
        trade.putInt("partnerColony", partnerColony);
        trade.putString("partnerDim", partnerDim.location().toString());
        trade.put("partnerPos", NbtUtils.writeBlockPos(partnerPos));
        trade.putInt("mode", mode);
        final ListTag mir = new ListTag();
        for (final UUID id : mirrored)
        {
            mir.add(NbtUtils.createUUID(id));
        }
        trade.put("mirrored", mir);
        final ListTag ord = new ListTag();
        for (final Order o : orders)
        {
            ord.add(o.save(provider));
        }
        trade.put("orders", ord);
        final ListTag tr = new ListTag();
        for (final Shipment s : transit)
        {
            tr.add(s.save(provider));
        }
        trade.put("transit", tr);
        tag.put("neoterraTrade", trade);
        return tag;
    }

    @Override
    public void deserializeNBT(@NotNull final HolderLookup.Provider provider, @NotNull final CompoundTag tag)
    {
        super.deserializeNBT(provider, tag);
        if (!tag.contains("neoterraTrade"))
        {
            return;
        }
        final CompoundTag trade = tag.getCompound("neoterraTrade");
        partnerColony = trade.getInt("partnerColony");
        partnerDim = dim(trade.getString("partnerDim"));
        partnerPos = NbtUtils.readBlockPos(trade, "partnerPos").orElse(BlockPos.ZERO);
        mode = trade.getInt("mode");
        mirrored.clear();
        for (final Tag t : trade.getList("mirrored", Tag.TAG_INT_ARRAY))
        {
            mirrored.add(NbtUtils.loadUUID(t));
        }
        orders.clear();
        for (final Tag t : trade.getList("orders", Tag.TAG_COMPOUND))
        {
            final Order o = Order.load(provider, (CompoundTag) t);
            if (o != null)
            {
                orders.add(o);
            }
        }
        transit.clear();
        for (final Tag t : trade.getList("transit", Tag.TAG_COMPOUND))
        {
            final Shipment s = Shipment.load(provider, (CompoundTag) t);
            if (s != null)
            {
                transit.add(s);
            }
        }
    }

    static ResourceKey<Level> dim(final String id)
    {
        final ResourceLocation rl = ResourceLocation.tryParse(id);
        return rl == null ? Level.OVERWORLD : ResourceKey.create(Registries.DIMENSION, rl);
    }

    // ------------------------------------------------------------------ records

    /** Goods a partner colony asked for. */
    public static final class Order
    {
        final UUID               token;
        final int                colony;
        final ResourceKey<Level> dim;
        final BlockPos           post;
        final ItemStack          stack;
        final int                count;

        Order(final UUID token, final int colony, final ResourceKey<Level> dim, final BlockPos post, final ItemStack stack, final int count)
        {
            this.token = token;
            this.colony = colony;
            this.dim = dim;
            this.post = post;
            this.stack = stack;
            this.count = count;
        }

        CompoundTag save(final HolderLookup.Provider provider)
        {
            final CompoundTag t = new CompoundTag();
            t.putUUID("token", token);
            t.putInt("colony", colony);
            t.putString("dim", dim.location().toString());
            t.put("post", NbtUtils.writeBlockPos(post));
            t.put("stack", stack.save(provider));
            t.putInt("count", count);
            return t;
        }

        @Nullable
        static Order load(final HolderLookup.Provider provider, final CompoundTag t)
        {
            final ItemStack stack = ItemStack.parseOptional(provider, t.getCompound("stack"));
            if (stack.isEmpty())
            {
                return null;
            }
            return new Order(t.getUUID("token"), t.getInt("colony"), dim(t.getString("dim")),
              NbtUtils.readBlockPos(t, "post").orElse(BlockPos.ZERO), stack, t.getInt("count"));
        }
    }

    /** Goods on the road. */
    static final class Shipment
    {
        final Order           order;
        final List<ItemStack> cargo;
        final long            arrival;

        Shipment(final Order order, final List<ItemStack> cargo, final long arrival)
        {
            this.order = order;
            this.cargo = cargo;
            this.arrival = arrival;
        }

        CompoundTag save(final HolderLookup.Provider provider)
        {
            final CompoundTag t = new CompoundTag();
            t.put("order", order.save(provider));
            final ListTag c = new ListTag();
            for (final ItemStack s : cargo)
            {
                c.add(s.save(provider));
            }
            t.put("cargo", c);
            t.putLong("arrival", arrival);
            return t;
        }

        @Nullable
        static Shipment load(final HolderLookup.Provider provider, final CompoundTag t)
        {
            final Order o = Order.load(provider, t.getCompound("order"));
            if (o == null)
            {
                return null;
            }
            final List<ItemStack> cargo = new ArrayList<>();
            for (final Tag s : t.getList("cargo", Tag.TAG_COMPOUND))
            {
                final ItemStack st = ItemStack.parseOptional(provider, (CompoundTag) s);
                if (!st.isEmpty())
                {
                    cargo.add(st);
                }
            }
            return new Shipment(o, cargo, t.getLong("arrival"));
        }
    }
}
