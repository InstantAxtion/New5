package com.neoterra.trade;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Leveling Staff.
 * <ul>
 *   <li>right-click a block: first corner – its height is the ground level, whatever the second corner's height;</li>
 *   <li>right-click another block: opposite corner;</li>
 *   <li>right-click in the air: the staff's menu – Flatten, Undo last flatten, Clear selection, Take stored blocks;</li>
 *   <li>sneak + right-click: flatten straight away;</li>
 *   <li>right-click a chest/barrel while the staff holds stored blocks: empties the store into it.</li>
 * </ul>
 * Selection and store live in the staff's custom data (the client draws the selection from it).
 */
public class LevelingStaffItem extends Item
{
    public static final int ACTION_FLATTEN = 1, ACTION_UNDO = 2, ACTION_CLEAR = 3, ACTION_TAKE = 4;

    public LevelingStaffItem(final Properties props)
    {
        super(props);
    }

    // ------------------------------------------------------------------------------------------------ data

    private static CompoundTag tag(final ItemStack stack)
    {
        final CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? new CompoundTag() : data.copyTag();
    }

    private static void save(final ItemStack stack, final CompoundTag tag)
    {
        if (tag.isEmpty())
        {
            stack.remove(DataComponents.CUSTOM_DATA);
        }
        else
        {
            stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        }
    }

    public static Optional<BlockPos> corner(final ItemStack stack, final String key)
    {
        final CompoundTag tag = tag(stack);
        return tag.contains(key) ? NbtUtils.readBlockPos(tag, key) : Optional.empty();
    }

    private static void setCorners(final ItemStack stack, final BlockPos a, final BlockPos b)
    {
        final CompoundTag tag = tag(stack);
        tag.remove("a");
        tag.remove("b");
        if (a != null)
        {
            tag.put("a", NbtUtils.writeBlockPos(a));
        }
        if (b != null)
        {
            tag.put("b", NbtUtils.writeBlockPos(b));
        }
        save(stack, tag);
    }

    /** The staff the player is using: held in either hand, else the first one in the inventory. */
    static ItemStack staff(final Player player)
    {
        for (final InteractionHand hand : InteractionHand.values())
        {
            if (player.getItemInHand(hand).getItem() instanceof LevelingStaffItem)
            {
                return player.getItemInHand(hand);
            }
        }
        for (int i = 0; i < player.getInventory().getContainerSize(); i++)
        {
            if (player.getInventory().getItem(i).getItem() instanceof LevelingStaffItem)
            {
                return player.getInventory().getItem(i);
            }
        }
        return ItemStack.EMPTY;
    }

    /** Holder of the blocks store: the staff, else a Builder's Wand (held first, then anywhere in the inventory). */
    static ItemStack storeHolder(final Player player)
    {
        final ItemStack staff = staff(player);
        if (!staff.isEmpty())
        {
            return staff;
        }
        for (final InteractionHand hand : InteractionHand.values())
        {
            if (player.getItemInHand(hand).getItem() instanceof BuilderWandItem)
            {
                return player.getItemInHand(hand);
            }
        }
        for (int i = 0; i < player.getInventory().getContainerSize(); i++)
        {
            if (player.getInventory().getItem(i).getItem() instanceof BuilderWandItem)
            {
                return player.getInventory().getItem(i);
            }
        }
        return ItemStack.EMPTY;
    }

    /** The staff's store of blocks that did not fit in the inventory. */
    public static Map<Item, Integer> store(final ItemStack stack)
    {
        return Flattening.readStore(tag(stack));
    }

    static Map<Item, Integer> store(final Player player)
    {
        return store(storeHolder(player));
    }

    // ------------------------------------------------------------------------------------------------ store management

    public static final int STORE_TAKE = 1, STORE_DISCARD = 2, STORE_TOGGLE_VOID = 3, STORE_DISCARD_ALL = 4;

    /** Item types the holder throws away instead of keeping (auto-discard). */
    public static java.util.Set<Item> voided(final ItemStack stack)
    {
        final java.util.Set<Item> out = new java.util.LinkedHashSet<>();
        final CompoundTag tag = tag(stack);
        if (tag.contains("void", net.minecraft.nbt.Tag.TAG_LIST))
        {
            final net.minecraft.nbt.ListTag list = tag.getList("void", net.minecraft.nbt.Tag.TAG_STRING);
            for (int i = 0; i < list.size(); i++)
            {
                final Item item = net.minecraft.core.registries.BuiltInRegistries.ITEM.get(net.minecraft.resources.ResourceLocation.parse(list.getString(i)));
                if (item != net.minecraft.world.item.Items.AIR)
                {
                    out.add(item);
                }
            }
        }
        return out;
    }

    static boolean isVoided(final Player player, final Item item)
    {
        final ItemStack holder = storeHolder(player);
        return !holder.isEmpty() && voided(holder).contains(item);
    }

    /**
     * A store action on a holder stack (staff or wand). Pure data change – used by the server and, for an immediate
     * screen update, by the client on its copy. Taking items into the inventory is done by the server only.
     */
    static void storeEdit(final ItemStack stack, final int action, final Item item, final int amount)
    {
        final CompoundTag tag = tag(stack);
        final Map<Item, Integer> store = Flattening.readStore(tag);
        switch (action)
        {
            case STORE_TAKE -> store.computeIfPresent(item, (k, v) -> Math.max(0, v - amount));
            case STORE_DISCARD -> store.remove(item);
            case STORE_DISCARD_ALL -> store.clear();
            case STORE_TOGGLE_VOID ->
            {
                final java.util.Set<Item> v = voided(stack);
                if (!v.remove(item))
                {
                    v.add(item);
                    store.remove(item);   // switching auto-discard on also throws away what is stored
                }
                final net.minecraft.nbt.ListTag list = new net.minecraft.nbt.ListTag();
                v.forEach(i -> list.add(net.minecraft.nbt.StringTag.valueOf(net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(i).toString())));
                if (list.isEmpty())
                {
                    tag.remove("void");
                }
                else
                {
                    tag.put("void", list);
                }
            }
            default -> { }
        }
        Flattening.writeStore(tag, store);
        save(stack, tag);
    }

    /** Server: a button of the Stored blocks screen. */
    static void storeAction(final Player player, final int action, final Item item, final int amount)
    {
        final ItemStack holder = storeHolder(player);
        if (holder.isEmpty())
        {
            return;
        }
        if (action == STORE_TAKE)
        {
            final int took = storeTake(player, item, amount);
            Flattening.giveInventoryOnly(player, item, took);
            return;
        }
        storeEdit(holder, action, item, amount);
    }

    static void storeAdd(final Player player, final Item item, final int count)
    {
        final ItemStack staff = storeHolder(player);
        if (staff.isEmpty())
        {
            Flattening.dropAt(player, item, count);
            return;
        }
        final CompoundTag tag = tag(staff);
        final Map<Item, Integer> store = Flattening.readStore(tag);
        store.merge(item, count, Integer::sum);
        Flattening.writeStore(tag, store);
        save(staff, tag);
    }

    /** Takes up to `count` of the item from the store; returns how many were taken. */
    static int storeTake(final Player player, final Item item, final int count)
    {
        final ItemStack staff = storeHolder(player);
        if (staff.isEmpty())
        {
            return 0;
        }
        final CompoundTag tag = tag(staff);
        final Map<Item, Integer> store = Flattening.readStore(tag);
        final int n = Math.min(count, store.getOrDefault(item, 0));
        if (n > 0)
        {
            store.put(item, store.get(item) - n);
            Flattening.writeStore(tag, store);
            save(staff, tag);
        }
        return n;
    }

    public static int storeTotal(final ItemStack stack)
    {
        return store(stack).values().stream().mapToInt(Integer::intValue).sum();
    }

    // ------------------------------------------------------------------------------------------------ use

    @Override
    public InteractionResult useOn(final UseOnContext ctx)
    {
        final Player player = ctx.getPlayer();
        if (player == null)
        {
            return InteractionResult.PASS;
        }
        if (ctx.getLevel().isClientSide)
        {
            return InteractionResult.SUCCESS;
        }
        final ItemStack stack = ctx.getItemInHand();
        if (player.isShiftKeyDown())
        {
            act(player, ACTION_FLATTEN);
            return InteractionResult.CONSUME;
        }
        final BlockPos pos = ctx.getClickedPos();
        final BlockEntity be = ctx.getLevel().getBlockEntity(pos);
        if (be instanceof Container container && storeTotal(stack) > 0)
        {
            final int moved = emptyInto(player, container);
            say(player, moved + " stored blocks put into the " + ctx.getLevel().getBlockState(pos).getBlock().getName().getString()
                + (storeTotal(stack) > 0 ? " – it is full, " + storeTotal(stack) + " still in the staff." : "."));
            return InteractionResult.CONSUME;
        }
        final Optional<BlockPos> a = corner(stack, "a");
        final Optional<BlockPos> b = corner(stack, "b");
        if (a.isEmpty() || b.isPresent())
        {
            setCorners(stack, pos, null);
            say(player, "Corner 1 set – the ground will be flattened to y " + pos.getY()
                + " (this block's height). Now right-click the opposite corner; its height doesn't matter.");
        }
        else
        {
            setCorners(stack, a.get(), pos);
            final int sx = Math.abs(pos.getX() - a.get().getX()) + 1;
            final int sz = Math.abs(pos.getZ() - a.get().getZ()) + 1;
            say(player, "Area " + sx + " x " + sz + ", ground level y " + a.get().getY() + " (from corner 1)."
                + (sx > Flattening.MAX_SIZE || sz > Flattening.MAX_SIZE ? " Too big – at most " + Flattening.MAX_SIZE + " x " + Flattening.MAX_SIZE + "." : " Sneak + right-click (or the menu) to flatten."));
        }
        return InteractionResult.CONSUME;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(final Level level, final Player player, final InteractionHand hand)
    {
        final ItemStack stack = player.getItemInHand(hand);
        if (player.isShiftKeyDown())
        {
            if (!level.isClientSide)
            {
                act(player, ACTION_FLATTEN);
            }
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
        }
        if (level.isClientSide)
        {
            LevelingStaffClient.openMenu(stack);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }

    /** A staff action from a click or a menu button (server side). */
    static void act(final Player player, final int action)
    {
        final ItemStack stack = action == ACTION_TAKE ? storeHolder(player) : staff(player);
        if (stack.isEmpty() || !(player.level() instanceof ServerLevel level))
        {
            return;
        }
        switch (action)
        {
            case ACTION_FLATTEN ->
            {
                final Optional<BlockPos> a = corner(stack, "a");
                final Optional<BlockPos> b = corner(stack, "b");
                if (a.isEmpty() || b.isEmpty())
                {
                    say(player, "Right-click two corners first.");
                    return;
                }
                final Flattening.Plan plan = Flattening.plan(level, player, a.get(), b.get());
                if (plan.refusal() != null)
                {
                    player.sendSystemMessage(Component.literal(plan.refusal()).withStyle(ChatFormatting.RED));
                    return;
                }
                Flattening.start(plan, player);
                setCorners(stack, null, null);
                say(player, "Flattening " + plan.sizeX() + " x " + plan.sizeZ() + " to y " + plan.ground()
                    + (plan.fillNeeded() > 0 ? " (" + plan.fillNeeded() + " blocks of fill used)" : "")
                    + ". Removed blocks: inventory" + (storeTotal(stack) > 0 ? ", the rest in the staff (" + storeTotal(stack) + ")" : "")
                    + ". Changed your mind? Use Undo in the staff's menu.");
            }
            case ACTION_UNDO ->
            {
                final String why = Flattening.undo(player);
                if (why != null)
                {
                    player.sendSystemMessage(Component.literal(why).withStyle(ChatFormatting.RED));
                }
                else
                {
                    say(player, "Undoing your last flatten – the land comes back, the blocks you got were taken back and your fill returned.");
                }
            }
            case ACTION_CLEAR ->
            {
                setCorners(stack, null, null);
                say(player, "Selection cleared.");
            }
            case ACTION_TAKE ->
            {
                int moved = 0;
                for (final Map.Entry<Item, Integer> e : store(stack).entrySet())
                {
                    final int before = player.getInventory().countItem(e.getKey());
                    final int took = storeTake(player, e.getKey(), e.getValue());
                    Flattening.giveInventoryOnly(player, e.getKey(), took);
                    moved += player.getInventory().countItem(e.getKey()) - before;
                }
                say(player, moved + " stored blocks moved to your inventory" + (storeTotal(stack) > 0 ? "; " + storeTotal(stack) + " still in the staff (inventory full)." : "."));
            }
            default -> { }
        }
    }

    /** Moves as much of the store as fits into a container. */
    private static int emptyInto(final Player player, final Container container)
    {
        int moved = 0;
        for (final Map.Entry<Item, Integer> e : store(storeHolder(player)).entrySet())
        {
            int left = e.getValue();
            for (int i = 0; i < container.getContainerSize() && left > 0; i++)
            {
                final ItemStack slot = container.getItem(i);
                final int max = e.getKey().getDefaultMaxStackSize();
                if (slot.isEmpty())
                {
                    final int n = Math.min(left, max);
                    container.setItem(i, new ItemStack(e.getKey(), n));
                    left -= n;
                }
                else if (slot.is(e.getKey()) && slot.getCount() < max && slot.getComponentsPatch().isEmpty())
                {
                    final int n = Math.min(left, max - slot.getCount());
                    slot.grow(n);
                    left -= n;
                }
            }
            final int done = e.getValue() - left;
            if (done > 0)
            {
                storeTake(player, e.getKey(), done);
                moved += done;
            }
        }
        container.setChanged();
        return moved;
    }

    static void say(final Player player, final String text)
    {
        player.displayClientMessage(Component.literal(text).withStyle(ChatFormatting.GOLD), false);
    }

    @Override
    public void appendHoverText(final ItemStack stack, final TooltipContext ctx, final List<Component> lines, final TooltipFlag flag)
    {
        lines.add(Component.literal("Right-click two corners – the first sets the ground height").withStyle(ChatFormatting.GRAY));
        lines.add(Component.literal("Right-click the air: menu (Flatten, Undo, Clear, Take)").withStyle(ChatFormatting.GRAY));
        lines.add(Component.literal("Sneak + right-click: flatten now").withStyle(ChatFormatting.GRAY));
        lines.add(Component.literal("Max " + Flattening.MAX_SIZE + " x " + Flattening.MAX_SIZE + "; fills holes with your dirt/stone").withStyle(ChatFormatting.DARK_GRAY));
        corner(stack, "a").ifPresent(p -> lines.add(Component.literal("Corner 1: " + p.getX() + " " + p.getY() + " " + p.getZ() + " (ground y " + p.getY() + ")").withStyle(ChatFormatting.GOLD)));
        corner(stack, "b").ifPresent(p -> lines.add(Component.literal("Corner 2: " + p.getX() + " " + p.getZ()).withStyle(ChatFormatting.GOLD)));
        final int stored = storeTotal(stack);
        if (stored > 0)
        {
            lines.add(Component.literal(stored + " blocks stored – right-click a chest to empty").withStyle(ChatFormatting.AQUA));
        }
    }
}
