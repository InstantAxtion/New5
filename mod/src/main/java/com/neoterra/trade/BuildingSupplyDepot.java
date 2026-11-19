package com.neoterra.trade;

import com.minecolonies.api.colony.IColony;
import com.minecolonies.api.colony.buildings.IBuilding;
import com.minecolonies.api.colony.requestsystem.request.IRequest;
import com.minecolonies.api.colony.requestsystem.request.RequestState;
import com.minecolonies.api.colony.requestsystem.requestable.Stack;
import com.minecolonies.api.colony.requestsystem.requestable.StackList;
import com.minecolonies.api.colony.requestsystem.token.IToken;
import com.minecolonies.api.colony.requestsystem.token.StandardToken;
import com.minecolonies.core.colony.buildings.AbstractBuilding;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Tuple;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemHandlerHelper;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.function.Predicate;

/**
 * Supply Depot. Its Quartermaster takes over requests nobody in the colony can fulfil (the ones that
 * would end up with the player), crafts them with an ordinary crafting recipe from ingredients the
 * colony delivers, and carries the result to whoever asked.
 */
public class BuildingSupplyDepot extends AbstractBuilding
{
    public static final String SCHEMATIC = "supplydepot";

    /** An order the Quartermaster works on. */
    public static final class Order
    {
        final UUID             token;
        final ResourceLocation recipe;
        final int              crafts;
        final ItemStack        result;     // one craft's output
        ItemStack              output = ItemStack.EMPTY;

        Order(final UUID token, final ResourceLocation recipe, final int crafts, final ItemStack result)
        {
            this.token = token;
            this.recipe = recipe;
            this.crafts = crafts;
            this.result = result;
        }

        public boolean crafted()
        {
            return !output.isEmpty();
        }
    }

    private final List<Order> orders = new ArrayList<>();
    private final Set<UUID>   failed = new HashSet<>();
    private int               tickCounter;

    public BuildingSupplyDepot(final IColony colony, final BlockPos pos)
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

    private int capacity()
    {
        return Math.max(1, getBuildingLevel()) * 3;
    }

    @Override
    public void onColonyTick(@NotNull final IColony colony)
    {
        super.onColonyTick(colony);
        if (getBuildingLevel() <= 0 || getAllAssignedCitizen().isEmpty() || ++tickCounter % 5 != 0
              || !NeoterraConfig.get(NeoterraConfig.SUPPLY_DEPOT, true))
        {
            return;
        }
        planOrders();
    }

    /** Take stuck requests the depot can craft. Returns how many new orders were taken. */
    int planOrders()
    {
        final IColony colony = getColony();
        final Level level = colony.getWorld();
        if (level == null)
        {
            return 0;
        }
        final List<IToken<?>> stuck = new ArrayList<>(colony.getRequestManager().getPlayerResolver().getAllAssignedRequests());
        stuck.addAll(colony.getRequestManager().getRetryingRequestResolver().getAllAssignedRequests());
        final Set<UUID> open = new HashSet<>();
        int taken = 0;
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
            final IBuilding requester = colony.getServerBuildingManager().getBuilding(request.getRequester().getLocation().getInDimensionLocation());
            if (requester instanceof BuildingSupplyDepot)
            {
                continue;   // our own ingredient requests: never craft for ourselves (no loops)
            }
            open.add(uuid);
            if (mirroredByTradePost(colony, uuid) || failed.contains(uuid) || orders.stream().anyMatch(o -> o.token.equals(uuid)) || orders.size() >= capacity())
            {
                continue;
            }
            final Optional<RecipeHolder<CraftingRecipe>> recipe = findRecipe(level, stack.getStack());
            if (recipe.isEmpty())
            {
                failed.add(uuid);
                continue;
            }
            final ItemStack result = recipe.get().value().getResultItem(level.registryAccess()).copy();
            final int crafts = (Math.max(1, stack.getCount()) + result.getCount() - 1) / result.getCount();
            orders.add(new Order(uuid, recipe.get().id(), crafts, result));
            requestIngredients(recipe.get().value(), crafts);
            taken++;
        }
        failed.retainAll(open);
        // requests resolved some other way: drop the order (ingredients that still arrive just stay in stock)
        orders.removeIf(o -> !o.crafted() && !open.contains(o.token));
        markDirty();
        return taken;
    }

    private static boolean mirroredByTradePost(final IColony colony, final UUID token)
    {
        return colony.getServerBuildingManager().getBuildings().values().stream()
          .anyMatch(b -> b instanceof BuildingTradePost post && post.isMirrored(token));
    }

    /** Is there a working depot in the colony that has taken, or will take, this request? (it has priority over trading) */
    static boolean willCraft(final IColony colony, final UUID token, final ItemStack wanted)
    {
        if (!NeoterraConfig.get(NeoterraConfig.SUPPLY_DEPOT, true) || colony.getWorld() == null)
        {
            return false;
        }
        boolean active = false;
        for (final IBuilding b : colony.getServerBuildingManager().getBuildings().values())
        {
            if (b instanceof BuildingSupplyDepot depot && depot.getBuildingLevel() > 0 && !depot.getAllAssignedCitizen().isEmpty())
            {
                if (depot.orders.stream().anyMatch(o -> o.token.equals(token)))
                {
                    return true;
                }
                if (!depot.failed.contains(token))
                {
                    active = true;
                }
            }
        }
        return active && findRecipe(colony.getWorld(), wanted).isPresent();
    }

    /** Simplest ordinary crafting recipe that makes this item (and doesn't use it as an ingredient). */
    static Optional<RecipeHolder<CraftingRecipe>> findRecipe(final Level level, final ItemStack wanted)
    {
        return level.getRecipeManager().getAllRecipesFor(RecipeType.CRAFTING).stream()
          .filter(h -> !h.value().isSpecial())
          .filter(h -> {
              final ItemStack out = h.value().getResultItem(level.registryAccess());
              return !out.isEmpty() && ItemStack.isSameItemSameComponents(out, wanted);
          })
          .filter(h -> h.value().getIngredients().stream().noneMatch(i -> !i.isEmpty() && i.test(wanted)))
          .filter(h -> h.value().getIngredients().stream().anyMatch(i -> !i.isEmpty()))
          .min(Comparator.comparingInt((RecipeHolder<CraftingRecipe> h) -> groups(h.value()).size()).thenComparing(h -> h.id().toString()));
    }

    /** Ingredients grouped: identical ingredient -> how many per craft. */
    static List<Tuple<Ingredient, Integer>> groups(final CraftingRecipe recipe)
    {
        final List<Tuple<Ingredient, Integer>> out = new ArrayList<>();
        for (final Ingredient ing : recipe.getIngredients())
        {
            if (ing.isEmpty())
            {
                continue;
            }
            final Tuple<Ingredient, Integer> same = out.stream().filter(t -> sameIngredient(t.getA(), ing)).findFirst().orElse(null);
            if (same == null)
            {
                out.add(new Tuple<>(ing, 1));
            }
            else
            {
                same.setB(same.getB() + 1);
            }
        }
        return out;
    }

    private static boolean sameIngredient(final Ingredient a, final Ingredient b)
    {
        final ItemStack[] x = a.getItems(), y = b.getItems();
        if (x.length != y.length)
        {
            return false;
        }
        for (int i = 0; i < x.length; i++)
        {
            if (!ItemStack.isSameItemSameComponents(x[i], y[i]))
            {
                return false;
            }
        }
        return true;
    }

    private void requestIngredients(final CraftingRecipe recipe, final int crafts)
    {
        for (final Tuple<Ingredient, Integer> g : groups(recipe))
        {
            final int total = g.getB() * crafts;
            final List<ItemStack> options = new ArrayList<>();
            for (final ItemStack s : g.getA().getItems())
            {
                final ItemStack one = s.copy();
                one.setCount(1);
                options.add(one);
            }
            if (options.size() == 1)
            {
                createRequest(new Stack(options.get(0), total, total), true);
            }
            else
            {
                createRequest(new StackList(options, "Supply Depot ingredient", total, total), true);
            }
        }
    }

    // ------------------------------------------------------------------ work

    /** An order whose ingredients are all in the depot, or null. */
    @Nullable
    public Order nextCraftable()
    {
        final IItemHandler handler = getItemHandlerCap();
        final Level level = getColony().getWorld();
        if (handler == null || level == null)
        {
            return null;
        }
        for (final Order o : orders)
        {
            if (o.crafted())
            {
                continue;
            }
            final Optional<RecipeHolder<?>> r = level.getRecipeManager().byKey(o.recipe);
            if (r.isEmpty() || !(r.get().value() instanceof CraftingRecipe recipe))
            {
                continue;
            }
            boolean ok = true;
            for (final Tuple<Ingredient, Integer> g : groups(recipe))
            {
                if (count(handler, g.getA()) < g.getB() * o.crafts)
                {
                    ok = false;
                    break;
                }
            }
            if (ok)
            {
                return o;
            }
        }
        return null;
    }

    /** Use up the ingredients and make the items. */
    public boolean craft(final Order o)
    {
        final IItemHandler handler = getItemHandlerCap();
        final Level level = getColony().getWorld();
        if (handler == null || level == null || o.crafted())
        {
            return false;
        }
        final Optional<RecipeHolder<?>> r = level.getRecipeManager().byKey(o.recipe);
        if (r.isEmpty() || !(r.get().value() instanceof CraftingRecipe recipe))
        {
            return false;
        }
        final List<ItemStack> remainders = new ArrayList<>();
        for (final Tuple<Ingredient, Integer> g : groups(recipe))
        {
            int left = g.getB() * o.crafts;
            for (int slot = 0; slot < handler.getSlots() && left > 0; slot++)
            {
                if (g.getA().test(handler.getStackInSlot(slot)))
                {
                    final ItemStack got = handler.extractItem(slot, left, false);
                    left -= got.getCount();
                    if (got.hasCraftingRemainingItem())
                    {
                        final ItemStack rem = got.getCraftingRemainingItem().copy();
                        rem.setCount(got.getCount());
                        remainders.add(rem);
                    }
                }
            }
        }
        for (final ItemStack rem : remainders)
        {
            ItemHandlerHelper.insertItemStacked(handler, rem, false);
        }
        o.output = o.result.copyWithCount(o.result.getCount() * o.crafts);
        markDirty();
        return true;
    }

    /** A crafted order that still has to be delivered, or null. */
    @Nullable
    public Order nextDelivery()
    {
        return orders.stream().filter(Order::crafted).findFirst().orElse(null);
    }

    /** Where the items of an order go (the building that asked), or the depot itself. */
    public IBuilding deliveryTarget(final Order o)
    {
        final IRequest<?> request = openRequest(o);
        if (request != null)
        {
            final IBuilding b = getColony().getServerBuildingManager().getBuilding(request.getRequester().getLocation().getInDimensionLocation());
            if (b != null)
            {
                return b;
            }
        }
        return this;
    }

    @Nullable
    private IRequest<?> openRequest(final Order o)
    {
        try
        {
            final IRequest<?> r = getColony().getRequestManager().getRequestForToken(new StandardToken(o.token));
            if (r != null && r.getState() != RequestState.COMPLETED && r.getState() != RequestState.CANCELLED
                  && r.getState() != RequestState.OVERRULED && r.getState() != RequestState.RECEIVED)
            {
                return r;
            }
        }
        catch (final IllegalArgumentException ignored)
        {
            // gone
        }
        return null;
    }

    /** Hand the items over at the target building and close the request. */
    public void deliver(final Order o, final IBuilding target)
    {
        final IItemHandler handler = target.getItemHandlerCap();
        final ItemStack first = o.output.copyWithCount(1);
        ItemStack rest = o.output.copy();
        if (handler != null)
        {
            rest = ItemHandlerHelper.insertItemStacked(handler, rest, false);
        }
        if (!rest.isEmpty())
        {
            final IItemHandler own = getItemHandlerCap();
            if (own != null)
            {
                rest = ItemHandlerHelper.insertItemStacked(own, rest, false);
            }
            if (!rest.isEmpty() && getColony().getWorld() != null)
            {
                final BlockPos p = getPosition().above();
                net.minecraft.world.Containers.dropItemStack(getColony().getWorld(), p.getX() + 0.5, p.getY(), p.getZ() + 0.5, rest);
            }
        }
        if (openRequest(o) != null)
        {
            first.setCount(o.output.getCount());
            getColony().getRequestManager().overruleRequest(new StandardToken(o.token), first);
        }
        orders.remove(o);
        markDirty();
    }

    private static int count(final IItemHandler handler, final Predicate<ItemStack> like)
    {
        int n = 0;
        for (int slot = 0; slot < handler.getSlots(); slot++)
        {
            final ItemStack s = handler.getStackInSlot(slot);
            if (!s.isEmpty() && like.test(s))
            {
                n += s.getCount();
            }
        }
        return n;
    }

    public int openOrders()
    {
        return orders.size();
    }

    /** Ingredients of open orders stay in the depot. */
    @Override
    public Map<Predicate<ItemStack>, Tuple<Integer, Boolean>> getRequiredItemsAndAmount()
    {
        final Map<Predicate<ItemStack>, Tuple<Integer, Boolean>> keep = super.getRequiredItemsAndAmount();
        final Level level = getColony().getWorld();
        if (level == null)
        {
            return keep;
        }
        for (final Order o : orders)
        {
            level.getRecipeManager().byKey(o.recipe).ifPresent(h -> {
                if (h.value() instanceof CraftingRecipe recipe)
                {
                    for (final Tuple<Ingredient, Integer> g : groups(recipe))
                    {
                        keep.put(g.getA(), new Tuple<>(g.getB() * o.crafts, false));
                    }
                }
            });
        }
        return keep;
    }

    // ------------------------------------------------------------------ saving

    @Override
    public CompoundTag serializeNBT(@NotNull final HolderLookup.Provider provider)
    {
        final CompoundTag tag = super.serializeNBT(provider);
        final ListTag list = new ListTag();
        for (final Order o : orders)
        {
            final CompoundTag t = new CompoundTag();
            t.putUUID("token", o.token);
            t.putString("recipe", o.recipe.toString());
            t.putInt("crafts", o.crafts);
            t.put("result", o.result.save(provider));
            if (!o.output.isEmpty())
            {
                t.put("output", o.output.save(provider));
            }
            list.add(t);
        }
        tag.put("neoterraDepot", list);
        return tag;
    }

    @Override
    public void deserializeNBT(@NotNull final HolderLookup.Provider provider, @NotNull final CompoundTag tag)
    {
        super.deserializeNBT(provider, tag);
        orders.clear();
        for (final Tag e : tag.getList("neoterraDepot", Tag.TAG_COMPOUND))
        {
            final CompoundTag t = (CompoundTag) e;
            final ItemStack result = ItemStack.parseOptional(provider, t.getCompound("result"));
            final ResourceLocation recipe = ResourceLocation.tryParse(t.getString("recipe"));
            if (result.isEmpty() || recipe == null)
            {
                continue;
            }
            final Order o = new Order(t.getUUID("token"), recipe, t.getInt("crafts"), result);
            if (t.contains("output"))
            {
                o.output = ItemStack.parseOptional(provider, t.getCompound("output"));
            }
            orders.add(o);
        }
    }
}
