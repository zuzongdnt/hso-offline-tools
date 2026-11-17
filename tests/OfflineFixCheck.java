import java.io.*;
import java.util.*;
import client.*;
import core.*;
import io.*;
import template.*;

public class OfflineFixCheck extends UpgradeCheck {
    static class Packets extends Capture {
        final List<byte[]> petPackets = new ArrayList<>();
        @Override public void addmsg(Message message) {
            super.addmsg(message);
            if (message.cmd == 44) petPackets.add(message.getData().clone());
        }
    }
    static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    static Message deposit(int slot) throws IOException {
        Message message = new Message(44);
        message.writer().writeByte(1);
        message.writer().writeShort(slot);
        message.writer().writeByte(3);
        message.writer().writeShort(1);
        return new Message((byte)44, message.getData());
    }
    static Item3 egg(int id) {
        ItemTemplate3 template=ItemTemplate3.item.get(id);
        Item3 item=new Item3();
        item.id=(short)id; item.name=template.getName(); item.type=14;
        item.clazz=4; item.icon=template.getIcon(); item.level=10;
        item.op=new ArrayList<>(); item.islock=true;
        return item;
    }
    public static void main(String[] args) throws Exception {
        UpgradeCheck.main(args);
        OfflineSkins.loadItems();
        OfflineSkins.loadFashion();
        ItemSellCoin.configure(Manager.gI().item7sell);
        Packets appearancePackets = new Packets();
        Funds appearance = new Funds(appearancePackets);
        appearance.fashion = new byte[]{-1,-1,-1,-1,-1,-1,-1};
        Item3 fashionHair = new Item3(); fashionHair.id = 4810; fashionHair.part = 121;
        appearance.item.wear[16] = fashionHair;
        Message fashionWire = new Message(0); Service.writeFashionParts(fashionWire, appearance);
        try (DataInputStream input = new DataInputStream(new ByteArrayInputStream(fashionWire.getData()))) {
            require(input.readByte()==7, "Wrong fashion part count");
            short[] parts = new short[7]; for (int i=0;i<7;i++) parts[i]=input.readShort();
            require(parts[2]==-2 && parts[5]==55 && Service.get_id_hair(appearance)==-1,
                    "Native hair must hide the helmet and use its directional part");
        }
        for (int id : new int[]{4807, 4808}) {
            Item3 converted = new Item3();
            converted.id = (short)id;
            converted.type = 25;
            converted.op = new ArrayList<>();
            OfflineSkins.refreshSavedItem(converted);
            appearance.item.wear[11] = converted;
            require(converted.type == 15 && Service.get_id_hair(appearance) == 159 + id - 4807
                    && OfflineSkins.bodyEffect(appearance) == 253 + id - 4807,
                    "Dream outfit must provide a body and idle sequence through the costume slot");
            require(ItemSellCoin.goldStock().stream().anyMatch(product -> product.id == id
                            && product.createItem().type == 15 && product.createItem().name.startsWith("Hiệp sĩ mộng mơ")),
                    "Dream outfit is missing from the gold costume shop");
        }
        Item3 outfit = new Item3(); outfit.id=4793; appearance.item.wear[11]=outfit;
        appearance.fashion = new byte[]{-55,-55,-55,-1,-1,-2,-1};
        fashionWire = new Message(0); Service.writeFashionParts(fashionWire, appearance);
        try (DataInputStream input = new DataInputStream(new ByteArrayInputStream(fashionWire.getData()))) {
            input.readByte(); input.readShort(); input.readShort();
            require(input.readShort()==201 && Service.get_id_hair(appearance)==-1,
                    "Outfit must show its complete head and suppress separately equipped hair");
        }
        for (int id : new int[]{4849,4854,4855,4858,4861,4862})
            require(OfflineSkins.removed(id), "Unverified cosmetic still enabled");
        require(ItemSellCoin.goldStock().stream().noneMatch(product -> OfflineSkins.removed(product.id)),
                "Removed cosmetics remain in the gold shop");
        System.out.println("PASS: original native hair direction, complete outfit priority and retired cosmetics.");

        require(stat(offer(4673), 0)==330 && stat(offer(4673), 40)==597
                && stat(offer(4673), 37)==2, "Sample orange Tinh Tu weapon differs from the recording");
        Item3 testWeapon = offer(4673);
        testWeapon.tier = 1;
        require(testWeapon.getParamByOptionId(37)==2, "Enhancement dropped Tinh Tu skill stat");
        int[] elemental = {2,4,1,3};
        for (int id : new int[]{4672,4673,4674,4675}) {
            Item3 weapon = offer(id);
            require(stat(weapon,0)>0 && stat(weapon,elemental[weapon.clazz])>0 && stat(weapon,37)==2,
                    "Tinh Tu weapon must keep both physical and class elemental damage");
        }
        for (int color = 0; color < 6; color++) {
            List<TinhTu.Offer> stock = TinhTu.offers(color);
            require(stock.size() == 64, "Missing equipment variants");
            for (TinhTu.Offer listing : stock) {
                require(listing.equals(TinhTu.findOffer(listing.key())), "Shop variant did not resolve");
                Item3 equipment = listing.createItem();
                for (int hole=58;hole<=60;hole++)
                    require(equipment.getParamByOptionId(hole)==-1,"Missing Tinh Tu shop socket");
                long hidden = equipment.op.stream().filter(o -> TinhTu.isHidden(Byte.toUnsignedInt(o.id))).count();
                require(hidden == (color >= 4 ? color-2 : 0), "Wrong number of hidden options");
                if (equipment.type == 1) require(stat(equipment,29)>0 || stat(equipment,30)>0,
                        "Tinh Tu pants or skirt missing regeneration");
            }
            for (int type : new int[]{3,6}) {
                require(stock.stream().map(TinhTu.Offer::createItem).anyMatch(item -> item.type == type
                        && stat(item,27)>0 && stat(item,28)>0 && stat(item,29)>0 && stat(item,30)>0) || color < 4,
                        "Gloves or boots missing the HP and MP variant");
            }
        }
        for (int id = 4746; id <= 4748; id++) {
            Item3 cloak = offer(id);
            int bonus = (4749 - id) * 500;
            for (int tier : new int[]{0, 15}) {
                cloak.tier = (byte) tier;
                for (int option : new int[]{7, 8, 9, 10, 11, 27, 28}) {
                    require(cloak.getParamByOptionId(option)==bonus, "Achievement cloak has wrong bonus");
                }
            }
        }
        Capture rewardPackets = new Capture();
        Funds recipient = new Funds(rewardPackets);
        recipient.point_active = new int[4];
        long initialGold = recipient.gold;
        core.OfflineRewards.checkIn(recipient);
        core.OfflineRewards.checkIn(recipient);
        require(recipient.gold==initialGold+2_000_000_000L && recipient.gems==300_000,
                "Two check-ins should add 2 billion gold and 200000 gems");
        event_daily.LoiDai.claimTestReward(recipient);
        event_daily.LoiDai.claimTestReward(recipient);
        require(recipient.point_active[4]==5 && RankBadge.effect(recipient)==98,
                "Test reward must set a persistent rank overlay");
        require(recipient.item.total_item_by_id(3,3596)==0 && recipient.item.total_item_by_id(4,206)==1,
                "Test reward must not occupy the fashion slot or repeat chests");
        for (int id=94;id<=98;id++) for (int zoom=1;zoom<=4;zoom++) {
            byte[] effect=java.nio.file.Files.readAllBytes(java.nio.file.Path.of("data/part_char/imgver/x"+zoom+"/111_"+id));
            int pngLength=java.nio.ByteBuffer.wrap(effect).getInt();
            require(pngLength>100 && pngLength<effect.length-20,"Invalid native badge sprite or metadata");
        }
        Item3 medal=offer(4587);medal.tier=9;
        GameSrc.revealMedalOptions(medal);
        require(medal.op.stream().noneMatch(o->o.id==96),"Medal still hides lines at +9");
        for (ItemSellCoin product:ItemSellCoin.goldStock()) {
            Item3 item=product.createItem();
            for (int hole=58;hole<=60;hole++)
                require(TinhTu.option(item,hole)==null,"A regular shop item received an empty socket");
        }
        recipient.item.bag3[0]=offer(4672);recipient.item.bag3[0].tier=15;recipient.item.bag3[0].level=135;
        recipient.item.bag3[1]=offer(4672);recipient.item.bag3[1].level=45;
        recipient.item_replace=0;recipient.item_replace2=1;
        require(GameSrc.validTransfer(recipient),"+15 cannot transfer to same type at a lower level");
        recipient.item.bag3[1]=offer(4656);
        require(!GameSrc.validTransfer(recipient),"Transfer accepted a different item type");
        recipient.item.bag3[0]=recipient.item.bag3[1]=null;
        recipient.maxbag = 256;
        recipient.item.bag3 = new Item3[256];
        recipient.item.bag47.clear();
        for (int i=0; i<256; i++) require(recipient.item.add_item_bag3(offer(4746)), "Slot rejected");
        recipient.item.char_inventory(3);
        require(java.nio.ByteBuffer.wrap(rewardPackets.packet).getShort(15)==256, "Inventory count overflowed");
        java.util.Arrays.fill(recipient.item.bag3, null);
        recipient.item.bag3[0] = offer(4746);
        GameSrc.rebuild_item(rewardPackets,request(0,0,3));
        require(recipient.id_item_rebuild==0, "Cloak could not be selected for enhancement");
        int initialGems=recipient.gems;
        GameSrc.rebuild_item(rewardPackets,request(2,0,1));
        require(recipient.gems==initialGems && recipient.item.bag3[0].tier==0,
                "Insufficient ingredients should leave gem balance and tier alone");
        for (short id : new short[]{0,1}) {
            Item47 stack = new Item47();
            stack.id=id; stack.quantity=1;
            recipient.item.add_item_bag47(7,stack);
        }
        recipient.gems=0;
        recipient.gold=3000L;
        GameSrc.rebuild_item(rewardPackets,request(2,0,0));
        require(recipient.item.bag3[0].tier==1 && recipient.gold==0,
                "Gold-only enhancement should consume 3000 gold and upgrade skin to +1");
        System.out.println("PASS: observed Tinh Tu samples, cloak bonuses, paid skin upgrade, repeated check-in and one-time badge.");

        int upgrades=0, failures=0;
        Packets connection=new Packets(); Funds player=new Funds(connection);
        for(short material=146;material<=150;material++) {
            Item47 stack=new Item47();stack.id=material;stack.category=7;stack.quantity=30000;
            player.item.bag47.add(stack);
        }
        int[] socketValues={27,406,-1};
        for(int level:new int[]{45,65,95,125}) {
            boolean success=false,failure=false;
            for(int attempt=0;attempt<150 && (!success || !failure);attempt++) {
                player.tinhtu_material=new short[]{146,147,148,149,150};
                Item3 item= TinhTu.offers(4).stream().filter(o -> o.itemId()==4672)
                        .findFirst().orElseThrow().createItem();
                item.level=(short)level;
                for(int i=0;i<3;i++) TinhTu.option(item,58+i).setParam(socketValues[i]);
                player.item.bag3[0]=item;
                GameSrc.Create_Medal(connection,request(4,0,3));
                for(int i=0;i<3;i++) {
                    final int socketId=58+i;
                    require(item.op.stream().filter(o->Byte.toUnsignedInt(o.id)==socketId).findFirst().orElseThrow().getParam(0)==socketValues[i],
                        "Socket "+socketId+" changed during Tinh Tu upgrade at level "+level);
                }
                boolean upgraded=item.level==level+10;
                success|=upgraded;failure|=!upgraded;
                if(upgraded) upgrades++; else failures++;
            }
            require(success && failure,"Missing success/failure coverage at level "+level);
        }
        Item3 lantern = new Item3();
        lantern.type = EquippedEffects.LANTERN_TYPE;
        lantern.op = new ArrayList<>();
        for (int option = 7; option <= 11; option++) lantern.op.add(new Option(option, 1000));
        for (byte clazz = 0; clazz < 4; clazz++) {
            Message encoded = new Message(0);
            lantern.writeItemOptions(encoded, clazz);
            var options = new DataInputStream(new ByteArrayInputStream(encoded.getData()));
            require(options.readUnsignedByte() == 5, "Lantern hides an elemental damage option");
            for (int option = 7; option <= 11; option++) {
                require(options.readUnsignedByte() == option && options.readInt() == 1000,
                        "Lantern did not send 10% damage of an element");
            }
        }
        Pet cat = Pet.get_pet(Pet.ID_CAT);
        require(cat.type == 14 && cat.icon == 45 && Pet.get_id(cat.type) == Pet.ID_CAT
                && cat.level == 30 && cat.grown == cat.maxgrown, "Cat egg does not round-trip to a max level cat");
        Pet lan = Pet.get_pet(Pet.ID_LAN);
        require(lan.type == 15 && lan.icon == 61 && Pet.get_id(lan.type) == Pet.ID_LAN
                && lan.level == 30 && lan.op.stream().anyMatch(opt -> opt.id == 1
                        && opt.param == 26355 && opt.maxdam == 31626), "Lan egg or ice damage did not round-trip");
        Item3 butterfly = new Item3(); butterfly.id = 4822;
        Item3 pig = new Item3(); pig.id = 4848;
        Item3 catArmor = new Item3(); catArmor.id = 4794;
        player.item.wear[14] = butterfly;
        player.item.wear[11] = catArmor;
        require(!EquippedEffects.pigWithButterfly(player) && EquippedEffects.pigGoldBonus(player) == 0,
                "Unpaired pig bonuses became active");
        player.item.wear[EquippedEffects.LANTERN_SLOT] = pig;
        require(EquippedEffects.pigWithButterfly(player) && EquippedEffects.pigGoldBonus(player) == 300,
                "Pig combinations are missing");
        player.item.wear[14] = player.item.wear[11] = player.item.wear[EquippedEffects.LANTERN_SLOT] = null;
        Pet oldCat = new Pet();
        oldCat.setup((org.json.simple.JSONArray) org.json.simple.JSONValue.parse(
                "[30,14,44,3,0,300,300,128,128,128,128,512,0,1,0,0,[]]"));
        require(oldCat.icon == 47 && oldCat.is_follow, "Saved cat did not keep its form and follow state");
        int[] eggs={2944,2943,2939,3269,3616,4617,4622,4626,4631,4699,4708,4761,4762,4768};
        for (int eggId : eggs) {
            Pet max = Pet.get_pet((short)eggId);
            require(max.level==30 && max.grown==max.maxgrown,"Hatched pet is not max level/growth");
            for (Option_pet stat:max.op) require(stat.id>=23 && stat.id<=26 ? stat.param==128 : stat.param==stat.maxdam,
                "New pet did not receive maximum stats");
        }
        for(int type=0;type<eggs.length;type++) {
            int id=eggs[type];
            Pet pet=Pet.get_pet((short)id);
            require(pet!=null,"Unsupported egg "+id);
            require(pet.type==type && Pet.get_id(pet.type)==id,"Pet/egg mapping does not round-trip: "+id);
            player.mypet=new ArrayList<>(); player.item.bag3[0]=egg(id);
            connection.petPackets.clear();
            Service.pet_process(connection,deposit(0));
            require(player.item.bag3[0]==null && player.mypet.size()==1,"Egg not deposited: "+id);
            require(player.mypet.get(0).time_born>System.currentTimeMillis(),"No incubation timer: "+id);
            require(connection.petPackets.size()==1,"Missing incubation response: "+id);
            DataInputStream packet=new DataInputStream(new ByteArrayInputStream(connection.petPackets.get(0)));
            require(packet.readUnsignedByte()==28 && packet.readUnsignedByte()==1 && packet.readUnsignedByte()==3 && packet.readUnsignedByte()==3,"Invalid pet container header");
            packet.readUTF(); packet.readByte(); require(packet.readShort()==id,"Wrong incubation egg");
            packet.readByte();packet.readShort();packet.readByte();packet.readShort();packet.readByte();packet.readByte();packet.readByte();
            require(packet.readUnsignedByte()==0,"Unexpected egg options");
            int minutes=packet.readInt();require(minutes>0 && minutes<=10,"Invalid hatch timer");packet.readByte();
            require(packet.available()==0,"Malformed pet item packet");
            player.item.bag3[0]=egg(id);
            Service.pet_process(connection,deposit(0));
            require(player.item.bag3[0]!=null && player.mypet.size()==1,"A second incubation consumed an egg");
        }
        player.mypet=new ArrayList<>();player.item.bag3[0]=offer(4672);
        Service.pet_process(connection,deposit(0));
        require(player.item.bag3[0]!=null && player.mypet.isEmpty(),"Non-egg consumed");
        Service.pet_process(connection,deposit(-1));Service.pet_process(connection,deposit(999));
        Pet existing=Pet.get_pet((short)2943);existing.is_hatch=false;existing.time_born=System.currentTimeMillis()+100000;
        player.mypet.add(existing);player.item.bag3[0]=egg(4626);
        Service.pet_process(connection,deposit(0));
        require(player.mypet.size()==2 && player.item.bag3[0]==null,"A non-incubating pet incorrectly blocks eggs");
        player.map = new map.Map(1, 0, new String[0], "HP test", (byte) 0, false, false, 1, 1, new ArrayList<>());
        player.map.players.add(player);
        player.body = new Body(player);
        player.kinhmach = new int[]{1, 0};
        player.tutien = new int[3];
        player.skill_point = new byte[11];
        player.list_eff = new ArrayList<>();
        int maxHp = (int) player.body.get_max_hp();
        player.hp = maxHp;
        for (int hit = 1; hit <= 3; hit++) {
            Service.usepotion(player, 0, -50);
            try (DataInputStream packet = new DataInputStream(new ByteArrayInputStream(connection.packet))) {
                require(packet.readByte() == 0 && packet.readShort() == player.id
                        && packet.readShort() == -1 && packet.readByte() == 0, "Invalid HP packet header");
                require(packet.readInt() == maxHp, "HP packet changed the maximum HP");
                require(packet.readInt() == maxHp - hit * 50, "HP packet did not report current HP");
            }
        }
        System.out.println("PASS: current HP falls across three ticks while the packet's maximum HP stays constant.");
        Item3 coat = new Item3();
        coat.id = 4656;
        coat.op = List.of(new Option(145, 299));
        player.item.wear[1] = coat;
        require(player.body.get_equipment_effect(133) == 0, "Tinh Tu effect enabled with only a coat");
        player.item.wear[6] = offer(4664);
        player.item.wear[7] = offer(4660);
        require(player.body.get_equipment_effect(133) == 299, "Complete group did not activate fire immunity");
        player.item.wear[7] = null;
        require(player.body.get_equipment_effect(133) == 0, "Removing a group item did not disable the effect");
        player.item.wear[0] = TinhTu.offers(4).stream().filter(o -> o.itemId()==4672)
                .findFirst().orElseThrow().createItem();
        int trueDamageChance = TinhTu.option(player.item.wear[0], 155).getParam(0);
        require(player.body.get_equipment_effect(155) == 0, "Shop hidden option enabled without rings");
        player.item.wear[3] = offer(4669);
        player.item.wear[9] = new Item3();
        player.item.wear[9].id = 3609;
        player.item.wear[9].op = List.of();
        require(player.body.get_equipment_effect(128) == trueDamageChance,
                "Moon ring did not activate the hidden option from the shop");
        player.item.wear[2] = TinhTu.offers(4).stream().filter(o -> o.itemId()==4668)
                .findFirst().orElseThrow().createItem();
        require(player.body.get_equipment_effect(166) == 0, "Shop glove activated on its own");
        player.item.wear[8] = offer(4671);
        player.item.wear[4] = new Item3();
        player.item.wear[4].id = 2940;
        player.item.wear[4].op = List.of();
        require(player.body.get_equipment_effect(166) == 100, "Moon necklace did not complete the gloves group");
        require(TinhTu.displayedOption(155, false)==155 && TinhTu.displayedOption(155, true)==128,
                "Hidden tooltip did not switch to the active option ID");
        Item3 broken = offer(4672);
        TinhTu.option(broken, 129).setParam(0);
        require(!TinhTu.canUpgrade(broken), "Zero durability still allows an upgrade");
        broken.color = 2;
        TinhTu.option(broken, 129).setParam(10000);
        require(!TinhTu.canUpgrade(broken), "Yellow Tinh Tu can be upgraded");
        ItemTemplate3 weapon = ItemTemplate3.item.get(4);
        List<Option> stats = List.of(new Option(0, 62), new Option(40, 136));
        weapon.setLevel((short) 1);
        weapon.setColor((byte) 4);
        WeaponStats.applyMaximum(weapon, stats);
        require(stats.get(0).getParam(0) == 76 && stats.get(0).getParam(15) == 212,
                "Weapon maximum or +15 scaling differs from the reference");
        require(stats.get(1).getParam(0) == 136, "Weapon's independent base damage changed");
        require(new Option(0, 650).getParam(11) == 1430, "Incorrect +11 multiplier");
        require(Skill.upgradePower(1) == 5 && Skill.upgradePower(10) == 35
                && Skill.upgradeSecondary(5, 2, 1000) == 210 && Skill.upgradeSecondary(5, 3, 1000) == 0,
                "Skill upgrade damage or target cap differs from the reference");
        System.out.println("PASS: Tinh Tu group activation, moon ring, upgrade restrictions, weapon maximums and skill progression.");
        System.out.println("PASS: "+upgrades+" successful Tinh Tu upgrades / "+failures+" failed attempts preserve three sockets; all 14 egg IDs deposit and round-trip; duplicate, non-egg and malformed requests preserve inventory.");
    }
}
