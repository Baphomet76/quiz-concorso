import "@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

export default {
  async fetch(req: Request) {
    if (req.method === "OPTIONS") {
      return new Response("ok", { headers: corsHeaders });
    }

    try {
      const { question, correctText } = await req.json();

      const apiKey = Deno.env.get("GEMINI_API_KEY");
      if (!apiKey) {
        return Response.json(
          { error: "Manca la chiave Gemini" },
          { status: 500, headers: corsHeaders }
        );
      }

      const prompt = `Rispondi in italiano, massimo 3 frasi. Domanda: ${question}. Risposta corretta: ${correctText}. Spiega solo perché questa risposta è giusta.`;

      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key=${apiKey}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
          }),
        }
      );

      const data = await res.json();
      const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || "Nessuna spiegazione disponibile.";

      return Response.json({ text }, { status: 200, headers: corsHeaders });
    } catch (error) {
      return Response.json(
        { error: "Payload non valido" },
        { status: 400, headers: corsHeaders }
      );
    }
  },
};
