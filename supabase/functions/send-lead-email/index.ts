import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
const cors = {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type","Access-Control-Allow-Methods":"POST, OPTIONS"};
Deno.serve(async (req) => {
 if(req.method==="OPTIONS") return new Response("ok",{headers:cors});
 try {
  if(req.method!=="POST") return new Response(JSON.stringify({error:"Method not allowed"}),{status:405,headers:{...cors,"Content-Type":"application/json"}});
  const auth=req.headers.get("Authorization")||"";
  const userClient=createClient(Deno.env.get("SUPABASE_URL")!,Deno.env.get("SUPABASE_ANON_KEY")!,{global:{headers:{Authorization:auth}}});
  const {data:{user},error:authError}=await userClient.auth.getUser();
  if(authError||!user) return new Response(JSON.stringify({error:"Unauthorized"}),{status:401,headers:{...cors,"Content-Type":"application/json"}});
  const {lead_id,subject,text}=await req.json();
  if(!lead_id||!subject||!text) return new Response(JSON.stringify({error:"lead_id, subject and text are required"}),{status:400,headers:{...cors,"Content-Type":"application/json"}});
  const admin=createClient(Deno.env.get("SUPABASE_URL")!,Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const {data:lead,error}=await admin.from("leads").select("*").eq("id",lead_id).eq("owner_id",user.id).single();
  if(error||!lead) return new Response(JSON.stringify({error:"Lead not found"}),{status:404,headers:{...cors,"Content-Type":"application/json"}});
  if(!lead.email) return new Response(JSON.stringify({error:"Lead has no email"}),{status:400,headers:{...cors,"Content-Type":"application/json"}});
  if(lead.status==="do_not_contact"||lead.consent_status==="opted_out") return new Response(JSON.stringify({error:"Contact is suppressed"}),{status:403,headers:{...cors,"Content-Type":"application/json"}});
  if(!["opted_in","legitimate_interest_reviewed"].includes(lead.consent_status)) return new Response(JSON.stringify({error:"Consent/legal basis must be reviewed before sending"}),{status:403,headers:{...cors,"Content-Type":"application/json"}});
  const apiKey=Deno.env.get("RESEND_API_KEY"),from=Deno.env.get("RESEND_FROM_EMAIL");
  if(!apiKey||!from) return new Response(JSON.stringify({error:"Configure RESEND_API_KEY and RESEND_FROM_EMAIL in Supabase secrets"}),{status:500,headers:{...cors,"Content-Type":"application/json"}});
  const response=await fetch("https://api.resend.com/emails",{method:"POST",headers:{"Authorization":"Bearer "+apiKey,"Content-Type":"application/json"},body:JSON.stringify({from,to:[lead.email],subject,text})});
  const result=await response.json();
  if(!response.ok) return new Response(JSON.stringify({error:result.message||"Resend request failed"}),{status:response.status,headers:{...cors,"Content-Type":"application/json"}});
  await admin.from("lead_email_log").insert({owner_id:user.id,lead_id:lead.id,provider:"resend",provider_message_id:result.id,recipient:lead.email,subject,status:"sent"});
  return new Response(JSON.stringify({ok:true,id:result.id}),{status:200,headers:{...cors,"Content-Type":"application/json"}});
 } catch(e) { return new Response(JSON.stringify({error:String(e)}),{status:500,headers:{...cors,"Content-Type":"application/json"}}); }
});
