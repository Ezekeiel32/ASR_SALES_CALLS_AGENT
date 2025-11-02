import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY as string });

export async function generateSummary(text: string): Promise<string> {
  const prompt = `
    Please provide a concise, professional summary in Hebrew for the following meeting transcript.
    The summary should be well-structured and easy to read.
    Format the output in Markdown.

    The output should include the following two sections:
    1.  **נקודות מרכזיות:** (Key Takeaways) - A bulleted list of the main points, decisions, and conclusions from the meeting.
    2.  **משימות לביצוע:** (Action Items) - A bulleted list of specific tasks, assigned individuals (if mentioned), and deadlines (if mentioned).

    If no specific action items are mentioned, state "לא צוינו משימות לביצוע.".

    Transcript:
    ---
    ${text}
    ---
  `;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
    });

    const summary = response.text;
    
    if (!summary) {
        console.error("No summary content in Gemini API response:", response);
        return "לא התקבל סיכום מהמודל.";
    }
    
    return summary;

  } catch (error) {
    console.error("Error generating summary with Gemini API:", error);
    return "שגיאה בעת יצירת הסיכום.";
  }
}
