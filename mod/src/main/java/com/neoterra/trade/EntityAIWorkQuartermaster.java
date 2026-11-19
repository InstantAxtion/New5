package com.neoterra.trade;

import com.minecolonies.api.colony.buildings.IBuilding;
import com.minecolonies.api.entity.ai.JobStatus;
import com.minecolonies.api.entity.ai.statemachine.AITarget;
import com.minecolonies.api.entity.ai.statemachine.states.IAIState;
import com.minecolonies.core.entity.ai.workers.AbstractEntityAIInteract;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import org.jetbrains.annotations.NotNull;

import static com.minecolonies.api.entity.ai.statemachine.states.AIWorkerState.IDLE;
import static com.minecolonies.api.entity.ai.statemachine.states.AIWorkerState.START_WORKING;

/** Quartermaster AI: craft orders whose ingredients have arrived, then carry them to whoever asked. */
public class EntityAIWorkQuartermaster extends AbstractEntityAIInteract<JobQuartermaster, BuildingSupplyDepot>
{
    enum QmState implements IAIState
    {
        CRAFT, DELIVER, WAIT;

        @Override
        public boolean isOkayToEat()
        {
            return this != DELIVER;
        }
    }

    private BuildingSupplyDepot.Order current;
    private int                       swings;

    public EntityAIWorkQuartermaster(@NotNull final JobQuartermaster job)
    {
        super(job);
        super.registerTargets(
          new AITarget(IDLE, START_WORKING, 20),
          new AITarget(START_WORKING, this::decideWork, 20),
          new AITarget(QmState.WAIT, this::waitAtDepot, 100),
          new AITarget(QmState.CRAFT, this::craft, 10),
          new AITarget(QmState.DELIVER, this::deliver, 20)
        );
        worker.setCanPickUpLoot(true);
    }

    @Override
    public Class<BuildingSupplyDepot> getExpectedBuildingClass()
    {
        return BuildingSupplyDepot.class;
    }

    private IAIState decideWork()
    {
        current = building.nextDelivery();
        if (current != null)
        {
            return QmState.DELIVER;
        }
        current = building.nextCraftable();
        if (current != null)
        {
            swings = 0;
            return QmState.CRAFT;
        }
        worker.getCitizenData().setJobStatus(JobStatus.IDLE);
        return QmState.WAIT;
    }

    private IAIState waitAtDepot()
    {
        if (!walkToBuilding())
        {
            return getState();
        }
        return START_WORKING;
    }

    private IAIState craft()
    {
        if (!walkToBuilding())
        {
            return getState();
        }
        worker.getCitizenData().setJobStatus(JobStatus.WORKING);
        if (swings++ < 4)
        {
            worker.swing(InteractionHand.MAIN_HAND);
            worker.playSound(SoundEvents.WOOD_HIT, 0.5F, 1.0F);
            return getState();
        }
        if (current != null && building.craft(current))
        {
            worker.getCitizenExperienceHandler().addExperience(0.5);
            return QmState.DELIVER;
        }
        return START_WORKING;
    }

    private IAIState deliver()
    {
        if (current == null || !current.crafted())
        {
            return START_WORKING;
        }
        final IBuilding target = building.deliveryTarget(current);
        if (!walkToBuilding(target))
        {
            return getState();
        }
        building.deliver(current, target);
        worker.playSound(SoundEvents.ITEM_PICKUP, 0.6F, 1.0F);
        current = null;
        return START_WORKING;
    }
}
