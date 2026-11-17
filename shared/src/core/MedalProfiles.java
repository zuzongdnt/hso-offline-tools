package core;

import template.Item3;
import template.Option;

/** Offline shop presets calibrated against the supplied +7/+10 references, not official roll ranges. */
public final class MedalProfiles {
    private MedalProfiles(){}
    public static void generated(Item3 item){
        int clazz=switch(item.id){case 4587->0;case 4589->1;case 4588->2;case 4590->3;default->-1;};
        if(clazz<0)return;
        int damage=clazz==1?4:clazz==2?1:0;
        item.op.removeIf(option->Byte.toUnsignedInt(option.id)<=4);
        item.op.add(new Option(damage,clazz==2?1309:817));
        put(item,7,2025);
        if(clazz==3){item.op.removeIf(option->option.id>=8&&option.id<=11);put(item,12,1896);put(item,25,12);}
        else put(item,8+new int[]{1,3,0,2}[clazz],1896);
        int special=new int[]{33,34,35,36}[clazz];put(item,special,272);
        put(item,37,1);put(item,38,1);
        item.clazz=4;
    }
    public static void refresh(Item3 item){
        if(item.type!=16||item.op==null)return;
        boolean damage800=item.op.stream().anyMatch(option->option.id>=0&&option.id<=4&&option.getParam(0)==800);
        boolean damage599=item.op.stream().anyMatch(option->option.id>=0&&option.id<=4&&option.getParam(0)==599);
        boolean merchant=damage800&&has(item,7,1000)&&has(item,27,1500)&&has(item,28,1000)&&has(item,37,2);
        boolean lottery=damage599&&has(item,27,1000)&&has(item,29,500)&&has(item,37,3)&&has(item,38,3)
                &&has(item,80,50)&&has(item,81,5000)&&has(item,82,50)&&has(item,87,50)&&has(item,88,3000)&&has(item,76,500)&&has(item,77,5000);
        if(merchant||lottery)generated(item);
    }
    private static boolean has(Item3 item,int id,int value){return item.op.stream().anyMatch(option->Byte.toUnsignedInt(option.id)==id&&option.getParam(0)==value);}
    private static void put(Item3 item,int id,int value){
        item.op.removeIf(option->Byte.toUnsignedInt(option.id)==id);item.op.add(new Option(id,value));
    }
}
