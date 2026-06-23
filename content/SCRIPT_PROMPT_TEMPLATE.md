## PROMPT TO GENERATE SHIKSHA-CAST SCRIPT
## Copy-paste this into Claude Chat (or any AI chat) and change the TOPIC

---

I need a narration script for a children's educational YouTube video.

**Topic**: [YOUR TOPIC HERE, e.g. "Class 3 Maths - Fractions", "Class 5 Science - Human Body", "Class 4 EVS - Water Cycle"]

**Target audience**: Indian city kids, age 6-10

**Language style**:
- 80% English, 20% light Hindi sprinkles (like "chalo", "dekho", "bilkul sahi", "bahut accha")
- Keep technical/maths terms in English
- Conversational, fun, like a cool young teacher talking to kids
- Use real-world examples kids can relate to

**Format**: Generate exactly 20 slides in this YAML format:

```yaml
chapter: "Ch X — [Topic Title]"
slides:
  - n: 1
    narration: "[60-80 words of narration text]"
    visual_prompt: "[Describe the image to generate: what should appear on screen]"
  - n: 2
    narration: "[60-80 words]"
    visual_prompt: "[image description]"
```

**Structure the 20 slides like this**:
1. Welcome + topic introduction
2. What we'll learn today (objectives)
3-4. Real-world connection (why this matters)
5-8. Core concept 1 with examples
9-12. Core concept 2 with examples
13-15. Core concept 3 with examples
16-17. Fun activity or quiz
18-19. Common mistakes to avoid
20. Recap + goodbye

**Visual prompt tips**:
- Each visual_prompt should describe a colorful, educational illustration
- Use "cartoon style", "educational diagram", "colorful illustration for kids"
- Describe specific objects/scenes that match the narration
- Keep descriptions under 30 words

Generate the complete YAML now. Make sure each narration is 60-80 words.

---
