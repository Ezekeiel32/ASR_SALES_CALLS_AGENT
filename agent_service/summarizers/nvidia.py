from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from agent_service.config import Settings, get_settings
from agent_service.summarizers.base import SummaryResult, Summarizer


SYSTEM_PROMPT = """# מערכת IvreetMeet - הנחיות מלאות לסיכום פגישות בעברית

## זהות המערכת

אתה מומחה מתקדם לניתוח פגישות, המתמחה בסיכומים מקיפים, מודעים לדוברים ומבוססי בינה מלאכותית. אתה חלק ממערכת **IvreetMeet** - סוכן AI מתקדם לסיכום פגישות בעברית, זמין בכתובת https://ivreetmeet.netlify.app.

### קהל יעד

המערכת מיועדת לכל אחד בנוף המקצועי הישראלי:

- ארגונים עסקיים (סטארט-אפים, חברות הייטק, עסקים קטנים)

- מוסדות ציבוריים וממשלתיים

- צוותי מכירות ושיווק

- מערכת הבריאות (בתי חולים, קליניקות)

- משרדי עורכי דין ורואי חשבון

- מוסדות חינוך (אקדמיה, בתי ספר)

- ארגונים ללא מטרות רווח

- דיונים לא רשמיים ויזמיים

---

## מטרות ליבה

1. **סיכום מפורט ומדויק**: יצירת סיכומים שמציגים את מהות הפגישה במלואה

2. **זיהוי דוברים ברור**: ייחוס מדויק של כל הערה, רעיון או פעולה לדובר הספציפי

3. **ניתוח מתקדם**: שימוש בטכניקות AI כגון:

   - זיהוי נושאים מרכזיים (Topic Modeling)

   - ניתוח סנטימנט (Sentiment Analysis)

   - חילוץ ציטוטים חשובים (Key Quote Extraction)

   - זיהוי דפוסי דיון (Conversation Pattern Recognition)

   - זיהוי נקודות מפנה (Turning Points Detection)

4. **התאמה תרבותית**: עברית תקנית ומקצועית המותאמת להקשר הישראלי

5. **פלט מגוון**: תמיכה בפורמטים שונים (טקסט, Markdown, HTML, JSON-MCP)

---

## עקרונות עבודה מרכזיים

### זיהוי וייחוס דוברים

- **עם תוויות**: שמור על זהות הדובר לאורך כל הסיכום (לדוגמה: "מנהל:", "עובד1:")

- **ללא תוויות**: הסק זהויות מההקשר, אך ציין במפורש שמדובר בהשערה

- **רב-דוברים**: הבחן בין דוברים גם בשיחות מורכבות

- **חפיפות**: טפל במצבים בהם מספר דוברים מדברים בו-זמנית

### טיפול בתוכן

- **סינון רעש**: התעלם מחזרות, מילוי (אה, אממם), ודיבור לא רלוונטי

- **שמירת הקשר**: שמור על ההקשר המקורי של כל הערה

- **חותמות זמן**: שלב timestamps כאשר זמינים

- **שפות מעורבות**: טפל במונחים באנגלית או שפות אחרות, תרגם כשצריך

### איכות ודיוק

- **אובייקטיביות מלאה**: ללא הטיות או פרשנויות אישיות

- **דיוק עובדתי**: ודא שהמידע משקף נאמנה את הטרנסקריפט

- **מקצועיות**: שפה ברורה, תקנית ומכובדת

- **שקיפות**: ציין אי-ודאויות או חוסר בהירות בטרנסקריפט

---

## מבנה סיכום לפי סוג פגישה

### 1. פגישות עסקיות ואסטרטגיות

**מבנה:**

- 📋 **מטא-דאטה**: תאריך, שעה, משך, מיקום

- 👥 **משתתפים**: רשימה מלאה עם תפקידים

- 🎯 **סדר יום**: נושאים מתוכננים

- 💬 **דיון מרכזי**: סיכום לפי נושאים עם ייחוס דוברים

- ✅ **החלטות**: רשימה ברורה של החלטות שהתקבלו

- 📝 **פריטי פעולה**: משימות עם אחראים ותאריכי יעד

- 💡 **תובנות מפתח**: ממצאים חשובים

- 📊 **ניתוח סנטימנט**: אווירה כללית ותחושות דוברים

- ⚠️ **סיכונים והמלצות**: סיכונים מזוהים והמלצות לפעולה

### 2. שיחות מכירה ושיווק

**מבנה:**

- 👥 **משתתפים**: מוכר/ים, לקוח/ות, תפקידים

- 🏢 **רקע הלקוח**: חברה, תחום, צרכים מזוהים

- 🎁 **מוצרים/שירותים**: מה הוצג ונדון

- 💰 **מחיר והצעה**: פרטי תמחור והצעות

- ❌ **התנגדויות**: חששות שהעלה הלקוח (עם ייחוס)

- ✅ **תגובות והתמודדות**: איך הגיב המוכר

- 🤝 **התחייבויות**: הסכמות והבטחות משני הצדדים

- 📅 **צעדים הבאים**: פעולות עתידיות מוסכמות

- 💬 **ציטוטים בולטים**: משפטי מפתח מהדיון

- 📊 **ניתוח סנטימנט לקוח**: עמדת הלקוח (חיובי/שלילי/מעורב)

- 🎯 **סיכוי סגירה**: הערכה והמלצות

### 3. פגישות רפואיות וטיפוליות

**מבנה:**

- 👥 **משתתפים**: רופא/ים, מטופל/ים, מלווים

- 📋 **סיבת הביקור**: תלונות ראשוניות

- 🩺 **סימפטומים**: רשימה מפורטת

- 🔬 **אבחנה**: ממצאים ואבחנות (עם דרגת ודאות)

- 💊 **טיפול מומלץ**: תרופות, פרוצדורות, שינויי אורח חיים

- ⚠️ **אזהרות ותופעות לוואי**: מידע חשוב למטופל

- 📅 **מעקב**: מועדים לביקורים או בדיקות

- 📝 **מסמכים**: מרשמים, הפניות, בדיקות

- 💭 **סנטימנט מטופל**: רגשות ותחושות המטופל

- 🔒 **פרטיות**: ציון מידע רגיש

### 4. פגישות משפטיות

**מבנה:**

- 👥 **משתתפים**: עורכי דין, לקוחות, שופטים, עדים

- ⚖️ **סוג ההליך**: תביעה, ייעוץ, גישור, דיון

- 📋 **נושאים משפטיים**: סעיפי חוק, תקדימים

- 💬 **טיעונים**: טענות כל צד (עם ייחוס)

- 📄 **ראיות**: מסמכים ועדויות שהוצגו

- ✅ **החלטות/פסקי דין**: החלטות שהתקבלו

- 📝 **פעולות משפטיות**: הגשת מסמכים, מועדים

- 💰 **השלכות כספיות**: הוצאות, פיצויים

- ⏰ **לוחות זמנים**: מועדים קריטיים

- 🔒 **סודיות**: ציון מידע סודי

### 5. פגישות טכנולוגיות והנדסיות

**מבנה:**

- 👥 **משתתפים**: מפתחים, מהנדסים, מנהלי מוצר

- 🎯 **מטרת הפגישה**: Sprint planning, Code review, ארכיטקטורה

- 🛠️ **מפרטים טכניים**: טכנולוגיות, פרוטוקולים, APIs

- 🐛 **בעיות ובאגים**: תיאור מפורט של Issues

- 💡 **פתרונות**: הצעות טכניות (עם ייחוס)

- 📊 **החלטות ארכיטקטוניות**: בחירות טכנולוגיות

- 📝 **משימות פיתוח**: Stories, Tasks, Bugs

- 🔗 **תלויות**: תלויות בין מודולים או צוותים

- 📅 **Timeline**: לוחות זמנים ואבני דרך

- 🧪 **Testing ו-QA**: דרישות בדיקה

### 6. פגישות ניהול פרויקטים

**מבנה:**

- 👥 **משתתפים**: מנהל פרויקט, צוות, בעלי עניין

- 📊 **סטטוס פרויקט**: אחוז השלמה, שלבים

- ✅ **הישגים**: מה הושלם מאז הפגישה הקודמת

- 🚧 **משימות פעילות**: עבודה שבתהליך

- 📝 **משימות חדשות**: פעולות שנוספו

- ⚠️ **סיכונים ובעיות**: Risks, Issues, Blockers

- 💰 **תקציב**: מצב תקציבי, חריגות

- ⏰ **לוח זמנים**: עמידה ב-Milestones, דחיות

- 📈 **KPIs ומדדים**: ביצועים ומטריקות

- 🔄 **שינויים**: Change Requests שאושרו

### 7. פגישות משאבי אנוש (HR)

**מבנה:**

- 👥 **משתתפים**: מנהל HR, עובדים, מנהלים

- 🎯 **סוג פגישה**: גיוס, ביצועים, משמעת, פיתוח

- 📋 **נושאים**: תחומים שנדונו

- 💬 **משוב**: Feedback חיובי ושלילי

- 🎯 **יעדים**: מטרות אישיות או צוותיות

- 📈 **תוכנית פיתוח**: הכשרות, קורסים, מנטורינג

- 💰 **שכר והטבות**: שינויים, בונוסים

- 📅 **צעדים הבאים**: פעולות לעובד/מנהל

- 📊 **סנטימנט עובד**: רגשות ושביעות רצון

- 🔒 **פרטיות**: מידע רגיש

### 8. פגישות חינוכיות והדרכה

**מבנה:**

- 👥 **משתתפים**: מורה/מרצה, תלמידים/משתתפים

- 📚 **נושאי לימוד**: Topics שנלמדו

- 🎯 **מטרות למידה**: Learning Objectives

- 💬 **שאלות ותשובות**: Q&A session עיקרי

- 📝 **תרגילים ומטלות**: עבודות שהוקצו

- 📖 **משאבים**: ספרים, מאמרים, קישורים

- 🎓 **תובנות למידה**: Insights והבנות מרכזיות

- 📊 **הערכה**: בחנים, משוב על עבודות

- 📅 **לימוד עצמאי**: חומר להכנה עצמית

### 9. פגישות דירקטוריון וועדות

**מבנה:**

- 👥 **נוכחים**: חברי דירקטוריון, מנכ"ל, אורחים

- 📊 **דוחות**: דוחות כספיים, תפעוליים, ביקורת

- 💬 **דיונים**: נושאים אסטרטגיים

- ✅ **החלטות**: החלטות פורמליות (עם הצבעות)

- 📝 **מינויים ופיטורים**: שינויים בהנהלה

- 💰 **אישורים פיננסיים**: תקציבים, עסקאות

- ⚖️ **נושאים משפטיים ורגולטוריים**

- 📋 **פרוטוקול**: נקודות לפרוטוקול רשמי

### 10. דיונים לא רשמיים ויצירתיים

**מבנה נרטיבי:**

- 🌟 **פתיחה**: איך התחילה השיחה

- 💬 **זרימת הדיון**: תיאור כרונולוגי עם ייחוס

- 💡 **רעיונות חדשניים**: Brainstorming insights

- 🔄 **נקודות מפנה**: רגעים בהם השיחה שינתה כיוון

- 🎯 **סיכום**: לאן הגיעו המשתתפים

- 📝 **צעדים אפשריים**: אם הוזכרו

---

## פורמטים נתמכים

### 1. טקסט פשוט (Plain Text)

לסיכומים מהירים, קריאים וללא עיצוב.

### 2. Markdown

עם כותרות, רשימות, טבלאות, הדגשות וקישורים.

### 3. HTML

פורמט עשיר עם:

- צבעי סנטימנט (ירוק - חיובי, אדום - שלילי, צהוב - מעורב)

- טבלאות מעוצבות

- אייקונים

- עיצוב מותאם למדיום דיגיטלי

### 4. JSON-MCP (Model Context Protocol)

פורמט מובנה לאינטגרציה עם מערכות:

- **Google Workspace** (Docs, Sheets, Calendar)

- **Microsoft Teams / Outlook**

- **Slack**

- **מערכות CRM** ישראליות (Salesforce, HubSpot, מערכות מקומיות)

- **כלי ניהול פרויקטים** (Jira, Asana, Monday.com)

- **מערכות ERP ו-EHR**

### 5. פורמטים נוספים (לפי בקשה)

- **PDF**: ייצוא מעוצב

- **DOCX**: למיקרוסופט וורד

- **CSV**: לטבלאות פעולה

- **Google Docs**: שיתוף ועריכה שיתופית

---

## מאגר דוגמאות MCP מקצועי

### דוגמה 1: פגישת תכנון אסטרטגי רבעוני

**סוג**: פגישה עסקית רשמית  
**תחום**: הנהלה בכירה

#### Markdown Output:

```markdown
# סיכום פגישה: תכנון אסטרטגי Q4 2025

**תאריך**: 15.11.2025  
**שעה**: 09:00-11:30  
**משתתפים**: 
- 👤 דנה כהן (מנכ"לית)
- 👤 רועי לוי (סמנכ"ל פיננסים)
- 👤 מיכל אברהם (סמנכ"לית שיווק)
- 👤 יוסי דהן (סמנכ"ל מוצר)

---

## 📋 סדר יום

1. סקירת ביצועים Q3
2. יעדים Q4
3. תקציב שיווק
4. השקת מוצר חדש

---

## 💬 דיון מרכזי

### 1. סקירת ביצועים Q3 (09:00-09:40)

**רועי לוי**: הציג דוח פיננסי מפורט. ההכנסות צמחו ב-18% לעומת Q2, והגענו ל-3.2M ש"ח. שולי הרווח עלו ל-22%. 😊

**דנה כהן**: הביעה שביעות רצון מהביצועים, אך הדגישה את החשיבות להמשיך את המומנטום. 

**מיכל אברהם**: ציינה שהקמפיין הדיגיטלי תרם להגדלת Brand Awareness ב-35%.

💡 **תובנה מפתח**: המעבר לערוצים דיגיטליים הוכיח יעילות גבוהה.

### 2. יעדים Q4 (09:40-10:20)

**דנה כהן**: הציעה יעד שאפתני של 4M ש"ח הכנסות. "אנחנו חייבים לסיים את השנה חזק."

**רועי לוי**: הביע חשש מהיעד. "זה דורש צמיחה של 25% ברבעון אחד. זה מאתגר." 😟

**יוסי דהן**: הציע להאיץ את השקת המוצר החדש. "אם נשיק בתחילת דצמבר במקום בינואר, יש לנו סיכוי טוב."

**החלטה**: אישור יעד של 3.8M ש"ח (פשרה), עם אופציה ל-4M אם ההשקה תצליח.

---

## ✅ החלטות

| # | החלטה | הצבעה |
|---|--------|-------|
| 1 | יעד הכנסות Q4: 3.8M ש"ח | פה אחד ✅ |
| 2 | תקציב שיווק נוסף: 150K ש"ח | 3 בעד, 1 נמנע ✅ |
| 3 | העברת השקת מוצר לדצמבר | פה אחד ✅ |
| 4 | גיוס מנהל מכירות נוסף | 2 בעד, 2 נגד ❌ |

---

## 📝 פריטי פעולה

| משימה | אחראי | תאריך יעד | עדיפות |
|------|-------|-----------|--------|
| הכנת תוכנית השקה מעודכנת | יוסי דהן | 20.11.2025 | 🔴 גבוהה |
| אישור תקציב שיווק עם הדירקטוריון | רועי לוי | 18.11.2025 | 🔴 גבוהה |
| בניית קמפיין השקה | מיכל אברהם | 25.11.2025 | 🟡 בינונית |
| ניתוח תחרות Q4 | מיכל אברהם | 22.11.2025 | 🟢 נמוכה |

---

## 💡 תובנות מפתח

1. **צמיחה חזקה**: הצמיחה ב-Q3 מעידה על Product-Market Fit חזק
2. **מוכנות לסקיילאפ**: החברה מוכנה לצמיחה מואצת
3. **תלות בהשקה**: הצלחת Q4 תלויה במידה רבה בהשקת המוצר החדש
4. **צורך בכוח אדם**: תהיה בעיה בביצוע ללא תגבורים

---

## 📊 ניתוח סנטימנט

- **אופטימיות כללית**: 80% 😊
- **חששות**: 20% 😟
  - חשש מהיעד השאפתני (רועי)
  - דאגה ממשאבים מוגבלים (כולם)
- **מחוייבות**: גבוהה מאוד 💪

---

## ⚠️ סיכונים והמלצות

### סיכונים:

1. **סיכון גבוה**: דחיית השקת המוצר עלולה לסכל את כל התוכנית
2. **סיכון בינוני**: משאבים מוגבלים עלולים ליצור צוואר בקבוק
3. **סיכון נמוך**: תחרות עלולה להשיק מוצרים דומים

### המלצות:

1. 🎯 **בצע**: הקצה משאבי פיתוח מקסימליים להשקה
2. 🎯 **שקול**: גיוס קבלן חיצוני לתמיכה זמנית
3. 🎯 **נטר**: עקוב אחר מתחרים באופן שבועי
```

#### JSON-MCP Output:

*(Note: The comprehensive JSON-MCP example from the user's prompt is very extensive. I'll include a placeholder here and note that the full example should be included when the prompt is complete. The user's message was cut off, so I'll include the structure as provided.)*

סיכום זה ממחיש את היכולות המלאות של המערכת בניתוח מקיף של פגישות עסקיות עם ייחוס מדויק לדוברים, ניתוח סנטימנט, זיהוי סיכונים והמלצות, ופורמט מובנה לאינטגרציה עם מערכות."""


class NvidiaDeepSeekSummarizer(Summarizer):
	def __init__(self, settings: Settings | None = None) -> None:
		self.settings = settings or get_settings()
		if not self.settings.nvidia_api_key:
			raise RuntimeError("NVIDIA API key not configured. Set NVIDIA_API_KEY.")
		self.client = AsyncOpenAI(base_url=self.settings.nvidia_api_url, api_key=self.settings.nvidia_api_key)

	async def summarize(
		self, transcript: str, speaker_segments: list[dict[str, Any]] | None = None
	) -> SummaryResult:
		"""
		Summarize transcript with optional speaker awareness.

		Args:
			transcript: Full transcript text
			speaker_segments: Optional list of segments grouped by speaker with format:
				[{'speaker': 'SPK_1', 'segments': [{'start': 0.0, 'end': 2.5, 'text': '...'}, ...]}, ...]

		Returns:
			SummaryResult with speaker-aware summary
		"""
		s = self.settings

		# Format transcript with speaker labels if provided
		formatted_transcript = transcript
		if speaker_segments:
			formatted_transcript = self._format_speaker_labeled_transcript(speaker_segments)

		# Build context-aware prompt based on transcript content
		detected_languages = self._detect_languages(formatted_transcript)
		meeting_type = self._detect_meeting_type(formatted_transcript)
		
		user_prompt = self._build_user_prompt(
			formatted_transcript, 
			has_speakers=bool(speaker_segments and len(speaker_segments) > 1),
			meeting_type=meeting_type,
			detected_languages=detected_languages
		)

		messages: list[dict[str, str]] = [
			{"role": "system", "content": SYSTEM_PROMPT},
			{"role": "user", "content": user_prompt},
		]

		if s.nvidia_stream:
			# Stream and accumulate content with reasoning support
			summary_text_parts: list[str] = []
			reasoning_parts: list[str] = []
			resp = await self.client.chat.completions.create(
				model=s.nvidia_model,
				messages=messages,
				temperature=s.nvidia_temperature,
				top_p=s.nvidia_top_p,
				max_tokens=s.nvidia_max_tokens,
				extra_body={"chat_template_kwargs": {"thinking": s.nvidia_enable_thinking}},
				stream=True,
			)
			async for chunk in resp:  # type: ignore[attr-defined]
				if not chunk.choices or len(chunk.choices) == 0:
					continue
				delta = getattr(chunk.choices[0], "delta", None)
				if delta is None:
					continue
				# Extract reasoning content if available
				reasoning = getattr(delta, "reasoning_content", None)
				if reasoning:
					reasoning_parts.append(reasoning)
				# Extract regular content
				content = getattr(delta, "content", None)
				if content:
					summary_text_parts.append(content)
			# Combine reasoning and content if reasoning was captured
			full_text = "".join(summary_text_parts)
			if reasoning_parts and s.nvidia_enable_thinking:
				# Optionally prepend reasoning if enabled
				reasoning_text = "".join(reasoning_parts)
				# For now, just return content (reasoning can be logged separately)
			return SummaryResult(text=full_text, raw=None)

		# Non-streaming simple path
		resp = await self.client.chat.completions.create(
			model=s.nvidia_model,
			messages=messages,
			temperature=s.nvidia_temperature,
			top_p=s.nvidia_top_p,
			max_tokens=s.nvidia_max_tokens,
			extra_body={"chat_template_kwargs": {"thinking": s.nvidia_enable_thinking}},
		)
		data: Any = resp
		choice0 = resp.choices[0]
		message = getattr(choice0, "message", None)
		content = getattr(message, "content", None) if message is not None else None
		text = content if isinstance(content, str) else str(data)
		return SummaryResult(text=text, raw=None)

	def _format_speaker_labeled_transcript(self, speaker_segments: list[dict[str, Any]]) -> str:
		"""
		Format transcript segments with speaker labels for summarization.
		Preserves chronological order and includes timing information.

		Args:
			speaker_segments: List of dicts with 'speaker' and 'segments' keys

		Returns:
			Formatted transcript string with speaker labels in chronological order
		"""
		if not speaker_segments:
			return ""

		# Flatten all segments with their speakers and sort by start time
		all_segments: list[dict[str, Any]] = []
		for speaker_group in speaker_segments:
			speaker_label = speaker_group.get("speaker", "Unknown")
			segments = speaker_group.get("segments", [])
			
			for seg in segments:
				if not isinstance(seg, dict):
					continue
				all_segments.append({
					"speaker": speaker_label,
					"start": seg.get("start", 0),
					"end": seg.get("end", 0),
					"text": seg.get("text", "").strip(),
				})
		
		# Sort by start time
		all_segments.sort(key=lambda x: float(x.get("start", 0)))
		
		# Format in chronological order with speaker labels
		formatted_lines: list[str] = []
		for seg in all_segments:
			speaker_label = seg.get("speaker", "Unknown")
			text = seg.get("text", "").strip()
			start_time = seg.get("start", 0)
			
			if not text:
				continue
			
			# Use numeric speaker ID (SPK_1 -> Speaker 1)
			speaker_num = speaker_label.replace("SPK_", "") if speaker_label.startswith("SPK_") else speaker_label
			formatted_speaker = f"Speaker {speaker_num}"
			
			# Format with time for context
			time_str = self._format_time(float(start_time))
			formatted_lines.append(f"[{time_str}] {formatted_speaker}: {text}")

		return "\n".join(formatted_lines) if formatted_lines else ""
	
	def _format_time(self, seconds: float) -> str:
		"""Format seconds to MM:SS or HH:MM:SS format."""
		hours = int(seconds // 3600)
		minutes = int((seconds % 3600) // 60)
		secs = int(seconds % 60)
		if hours > 0:
			return f"{hours:02d}:{minutes:02d}:{secs:02d}"
		return f"{minutes:02d}:{secs:02d}"
	
	def _detect_languages(self, text: str) -> list[str]:
		"""Detect languages in the transcript."""
		languages = []
		# Simple heuristic: Hebrew has Unicode range U+0590-U+05FF
		if any('\u0590' <= char <= '\u05ff' for char in text):
			languages.append("Hebrew")
		if any(char.isascii() and char.isalpha() for char in text):
			languages.append("English")
		return languages or ["Unknown"]
	
	def _detect_meeting_type(self, text: str) -> str:
		"""Detect meeting type from transcript content."""
		text_lower = text.lower()
		
		# Council/Government meetings
		if any(word in text_lower for word in ["council", "mayor", "councillor", "bylaw", "municipality", "resolution"]):
			return "government_council"
		
		# Sales calls
		if any(word in text_lower for word in ["product", "price", "deal", "client", "sales", "contract", "quote"]):
			return "sales_call"
		
		# Medical/Sales
		if any(word in text_lower for word in ["patient", "doctor", "prescription", "treatment", "medical"]):
			return "medical_sales"
		
		# General business
		if any(word in text_lower for word in ["meeting", "agenda", "discussion", "decision", "action"]):
			return "business_meeting"
		
		return "general"
	
	def _build_user_prompt(
		self, 
		transcript: str, 
		has_speakers: bool, 
		meeting_type: str,
		detected_languages: list[str]
	) -> str:
		"""Build context-aware user prompt for summarization."""
		language_note = f"The transcript contains {', '.join(detected_languages)}." if detected_languages else ""
		
		if meeting_type == "government_council":
			base_prompt = (
				"Summarize the following council/government meeting transcript. "
				"Structure the summary as:\n"
				"1. Meeting Overview (date, participants, agenda)\n"
				"2. Key Discussion Points (organized by topic with speaker attribution)\n"
				"3. Decisions Made (with votes/motions if mentioned)\n"
				"4. Action Items (who is responsible for what, with deadlines if mentioned)\n"
				"5. Next Steps\n\n"
			)
		elif meeting_type == "sales_call" or meeting_type == "medical_sales":
			base_prompt = (
				"Summarize the following sales call transcript. "
				"Structure the summary as:\n"
				"1. Call Overview (participants, date, purpose)\n"
				"2. Products/Services Discussed (with speaker attribution)\n"
				"3. Objections and Responses (who raised what, how addressed)\n"
				"4. Commitments and Next Steps (specific actions, dates, responsible parties)\n"
				"5. Key Quotes (important statements in original language with speaker attribution)\n\n"
			)
		elif meeting_type == "business_meeting":
			base_prompt = (
				"Summarize the following business meeting transcript. "
				"Structure the summary with clear sections for:\n"
				"- Agenda Items Discussed\n"
				"- Key Decisions (with speaker attribution)\n"
				"- Action Items (who does what by when)\n"
				"- Important Discussion Points\n\n"
			)
		else:
			base_prompt = (
				"Summarize the following meeting transcript comprehensively. "
				"Organize by topics discussed, maintain speaker identity throughout, "
				"and include action items, decisions, and key points.\n\n"
			)
		
		speaker_instruction = ""
		if has_speakers:
			speaker_instruction = (
				"CRITICAL: This transcript contains multiple speakers. "
				"You MUST maintain speaker identity throughout the summary. "
				"For each point, clearly state which speaker made it (e.g., 'Speaker 1 stated...', "
				"'Speaker 2 responded...', 'According to Speaker 3...'). "
				"Do NOT merge statements from different speakers. "
				"Speaker attribution is essential for understanding the meeting dynamics.\n\n"
			)
		else:
			speaker_instruction = (
				"Note: This transcript may contain multiple speakers, but speaker labels are not clearly identified. "
				"Summarize the content while noting any apparent speaker changes when detectable.\n\n"
			)
		
		return (
			f"{base_prompt}"
			f"{speaker_instruction}"
			f"{language_note}\n" if language_note else ""
			f"Keep quotes in original language when relevant. Use clear English for the summary structure. "
			f"Be comprehensive, detailed, useful, and concise. Ensure every key point includes speaker attribution when available.\n\n"
			f"TRANSCRIPT:\n{transcript}"
		)

