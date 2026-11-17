package core;

import client.Player;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Set;
import template.EffTemplate;
import template.Item3;
import template.Option;
import template.TinhTu;

/** One table feeds socket tooltips and combat. Percentages use basis points. */
public final class SocketGems {
    private SocketGems() {}
    private static final int[] ABSORB={50,100,150,250,350};
    private static final int[] PHONG_REFINED={150,200,250,350,450};
    private static final int[] HP_LIMIT={2000,3000,4000,5000,7000};
    private static final int[] HEAL={100,200,500,700,1000};
    private static final int[] SINH={200,250,300,350,450};
    private static final int[] CRIT={300,500,700,900,1400};
    private static final int[] COMBO={100,300,500,700,900};
    public static final Set<Integer> DEBUFFS=Set.of(-121,-122,-123,-124,-201,-202,-205,-206,-228,-230,-232,-236,4);
    public static int kind(int id){return id>=352&&id<=411?(id-(id<382?352:382))/5:id>=412&&id<=416?6:-1;}
    private static int rank(int id){return (id-(id>=412?412:id>=382?382:352))%5;}
    private static boolean socket(Option option){int id=Byte.toUnsignedInt(option.id);return id>=58&&id<=60;}
    private static void add(int[] values,int[] counts,int gem){
        int kind=kind(gem);if(kind<0)return;int rank=rank(gem);counts[kind]++;
        switch(kind){
            case 0,1:values[kind]+=25-rank*5;break;
            case 2:values[2]+=ABSORB[rank];break;
            case 3:values[3]+=(gem>=382?PHONG_REFINED:ABSORB)[rank];values[4]+=HP_LIMIT[rank];values[5]+=HEAL[rank];break;
            case 4:values[6]+=SINH[rank];break;
            case 5:values[7]+=CRIT[rank];break;
            case 6:values[8]+=COMBO[rank];break;
        }
    }
    private static int[] stats(Item3[] items){
        int[] values=new int[9],counts=new int[7];
        for(Item3 item:items)if(item!=null&&item.op!=null)for(Option option:item.op)
            if(socket(option))add(values,counts,option.getParam(0));
        if(counts[0]>0)values[0]/=counts[0];if(counts[1]>0)values[1]/=counts[1];
        if(counts[3]>0){values[4]/=counts[3];values[5]/=counts[3];}
        return values;
    }
    public static int value(Item3 item,int option){return option>=100&&option<=108?stats(new Item3[]{item})[option-100]:0;}
    private static int[] stats(Player p){return stats(p.item.wear);}
    public static int threshold(Player p,int first){
        if(first==352||first==382)return stats(p)[0];
        if(first==357||first==387)return stats(p)[1];
        return 0;
    }
    public static int resistancePenalty(Player p,int chance){
        EffTemplate immunity=p.get_eff(-211);
        return immunity!=null&&immunity.param==20?Math.max(0,chance-2000):chance;
    }
    private static boolean has(Player p,int kind,boolean refined){
        for(Item3 item:p.item.wear)if(item!=null&&item.op!=null)for(Option option:item.op){
            int id=option.getParam(0);if(socket(option)&&kind(id)==kind&&(id>=382)==refined)return true;
        }
        return false;
    }
    public static void rebuild(Item3 item){
        if(item.op==null)return;int[] values=stats(new Item3[]{item});
        item.op.removeIf(option->{int id=Byte.toUnsignedInt(option.id);return id>=100&&id<=108;});
        for(int i=0;i<values.length;i++)if(values[i]>0)item.op.add(new Option(100+i,values[i]));
    }
    public static void hon(Player p)throws IOException {
        int required=stats(p)[0];if(required==0||p.get_eff(-210)!=null)return;
        if(++p.hit_count_ngoc_hon_nguyen<required)return;p.hit_count_ngoc_hon_nguyen=0;
        // A remaining unrefined socket retains its drawback.
        if(has(p,0,false)){p.hp=Math.max(1,p.hp-p.body.get_max_hp()/2);Service.usepotion(p,0,0);}
        p.add_eff(-210,200,3000);CombatVisuals.show(p,20,3000);
    }
    public static void khai(Player p)throws IOException {
        int required=stats(p)[1];if(required==0||p.get_eff(-211)!=null)return;
        if(++p.hit_count_ngoc_khai_hoan<required)return;p.hit_count_ngoc_khai_hoan=0;
        synchronized(p.list_eff){p.list_eff.removeIf(effect->DEBUFFS.contains(effect.id));}
        p.add_eff(-211,has(p,1,false)?20:1,3000);CombatVisuals.show(p,45,3000);
    }
    public static void absorb(Player p){
        int chance=stats(p)[2];if(chance==0||p.get_eff(-213)!=null||!TinhTu.rolls(chance))return;
        p.add_eff(-213,10,3000);
        if(has(p,2,false))p.add_eff(-216,1,3000);
        visual(p,20,3000);
    }
    private static void visual(Player p,int effect,int duration){
        try{CombatVisuals.show(p,effect,duration);}catch(IOException error){System.err.println("Socket visual: "+error.getMessage());}
    }
    public static long attackDamage(Player p,long damage,boolean bossOrPlayer,boolean monster)throws IOException {
        if(damage<=0)return damage;
        int[] values=stats(p);if(bossOrPlayer)hon(p);
        if(p.get_eff(-212)==null&&values[3]>0&&p.hp<p.body.get_max_hp()*values[4]/10000&&TinhTu.rolls(values[3])){
            int duration=has(p,3,true)?5000:3000;p.add_eff(-212,values[5],duration);visual(p,27,duration);
        }
        EffTemplate heal=p.get_eff(-212);
        if(heal!=null&&p.get_eff(-216)==null){
            long amount=p.body.get_max_hp()*heal.param/10000;Service.usepotion(p,0,amount);
        }
        if(p.get_eff(-214)==null&&TinhTu.rolls(values[6])){
            p.add_eff(-214,50,3000);if(has(p,4,false))p.add_eff(-215,20,3000);visual(p,29,3000);
        }
        if(p.get_eff(-210)!=null)damage*=2;
        if(p.get_eff(-214)!=null){if(bossOrPlayer&&monster)damage=damage*150/100;else if(monster&&p.get_eff(-215)!=null)damage=damage*80/100;}
        if(TinhTu.rolls(values[8])){damage*=2;visual(p,18,800);}
        return Math.min(2_000_000_000L,damage);
    }
    public static void defend(Player p)throws IOException {
        absorb(p);khai(p);
        int chance=p.body.get_equipment_effect(80);
        if(p.get_eff(-203)==null&&TinhTu.rolls(chance)){p.add_eff(-203,30,5000);visual(p,19,5000);}
    }
}
