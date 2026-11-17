package core;

import client.Pet;
import client.Player;
import java.util.ArrayList;
import template.Item3;
import template.ItemTemplate3;
import template.Option;

public final class ArenaBotEquipment {
    private ArenaBotEquipment() {}
    public static int wingTier(int level) {
        return level < 65 ? -1 : level < 75 ? 5 : level < 85 ? 15 : level < 90 ? 25 : 30;
    }
    public static void configure(Player bot) {
        bot.item.wear[12] = OfflineMarket.lotteryMedal(bot.clazz);
        int tier = wingTier(bot.level);
        if (tier < 0) { bot.item.wear[10] = null;bot.item.wear[14] = null; }
        else {
            int base = new int[]{2880,2901,2915,2887}[bot.clazz];
            ItemTemplate3 template = ItemTemplate3.item.get(base);
            Item3 wing = new Item3();wing.id=(short)base;wing.name=template.getName();
            wing.type=7;wing.clazz=4;wing.icon=template.getIcon();wing.color=5;
            wing.level=60;wing.tier=(byte)tier;wing.islock=true;wing.op=new ArrayList<>();
            for (int step=0;step<=tier/5;step++) {
                ItemTemplate3 stage = ItemTemplate3.item.get(base+step);
                wing.part=stage.getPart();
                for (Option option:stage.getOp()) wing.op.add(new Option(option.id,option.getParam(0)));
            }
            wing.op.add(new Option(41,200));wing.op.add(new Option(42,6000));
            bot.item.wear[10]=wing;
        }
        Pet pet = Pet.get_pet((short)new int[]{3269,3616,4617,4622}[bot.clazz]);
        pet.level=(short)Math.min(30,Math.max(1,(bot.level-40)/3));
        pet.point1=pet.point2=pet.point3=pet.point4=(short)(pet.level*5);
        for (template.Option_pet option:pet.op) {
            option.param=Math.max(1,(int)((long)option.param*pet.level/30));
        }
        pet.is_hatch=false;pet.is_follow=true;pet.time_born=System.currentTimeMillis()-86400000L;
        bot.mypet.add(pet);bot.pet_follow=true;
    }
}
