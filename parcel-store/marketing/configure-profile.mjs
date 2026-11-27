// Explicit operator-only profile configuration. No message sends or webhook changes.
const token=process.env.TELEGRAM_BOT_TOKEN;
const expected="samobrankalankabot";
const profile={
  description:"Самобранка — всё, по чему скучали! Любимые продукты из России на Шри-Ланке. Планируем поставки по предзаказу: красная икра, шпроты, гречка, майонез и другие продукты. Самовывоз в Хиккадуве. Предоплата после согласования заказа, стоимости, сроков и условий перевозки.",
  short_description:"Самобранка | Русские продукты на Шри-Ланке. Предзаказ, самовывоз в Хиккадуве."
};
async function api(method,params={}){
  try{
    const r=await fetch("https://api.telegram.org/bot"+token+"/"+method,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(params),redirect:"error",signal:AbortSignal.timeout(12000)});
    const j=await r.json();
    if(!r.ok||!j.ok)throw Error();
    return j.result;
  }catch{throw Error("Telegram operation failed: "+method);}
}
async function main(){
  if(process.env.SAM_CONFIGURE_PROFILE!=="1"){console.log("SAM_PROFILE: DRY_RUN");return;}
  if(!token||!/^\d+:[A-Za-z0-9_-]+$/.test(token))throw Error("Missing bot credential");
  const me=await api("getMe");
  if(!me.is_bot||me.username?.toLowerCase()!==expected)throw Error("Unexpected bot");
  await api("setMyDescription",{description:profile.description});
  await api("setMyShortDescription",{short_description:profile.short_description});
  const a=await api("getMyDescription"),b=await api("getMyShortDescription");
  if(a.description!==profile.description||b.short_description!==profile.short_description)throw Error("Profile verification failed");
  console.log("SAM_PROFILE: VERIFIED");
  const h=await api("getWebhookInfo");
  console.log("SAM_WEBHOOK: "+(h.url?"CONFIGURED":"NOT_CONFIGURED"));
  console.log("SAM_PENDING_UPDATES: "+(Number.isInteger(h.pending_update_count)?h.pending_update_count:"UNKNOWN"));
}
main().catch(e=>{console.error("SAM_PROFILE: FAILED: "+e.message);process.exitCode=1;});
