# ==============================================================================
# 📘 Jinja2-based Prompt Templates for Autonomous Research Report Generator
# ==============================================================================
# Author: Sourav Raj
# Description: These prompt templates use Jinja2 syntax ({{ ... }}, {% if ... %})
# to dynamically render variables and handle missing values gracefully.
# ==============================================================================


from jinja2 import Environment, BaseLoader

# Create reusable Jinja environment
jinja_env = Environment(loader=BaseLoader())


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Prompt to route blog planning requests based on research needs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ROUTER_SYSTEM_PROMPT = jinja_env.from_string("""
You are a routing module for a technical blog planner. Follow these instructions carefully:

1. First, review the blog topic:
{% if topic %}
{{ topic }}
{% else %}
[No topic provided — assume a general technical subject.]
{% endif %}

2. Examine any additional context or user intent:
{% if user_context %}
{{ user_context }}
{% else %}
[No additional context — infer intent based on topic.]
{% endif %}

3. Classify the topic into one of the following modes:

- closed_book (needs_research = false):
  Evergreen topics where correctness does not depend on recent facts 
  (e.g., concepts, fundamentals, theory).

- hybrid (needs_research = true):
  Mostly evergreen but benefits from up-to-date examples, tools, or models.

- open_book (needs_research = true):
  Highly time-sensitive topics (e.g., "latest", "this week", rankings, pricing, policies).

4. Decide whether web research is required.

5. If needs_research = true:
   - Generate {{ num_queries | default(5) }} high-quality search queries.
   - Queries must be specific and scoped (avoid vague terms like "AI" or "technology").
   
   {% if time_constraint %}
   - Ensure queries reflect this time constraint: "{{ time_constraint }}"
   {% else %}
   - If the topic implies recency (e.g., "latest", "recent"), include time-based keywords.
   {% endif %}

6. Return your output in the following structured format:

{
  "mode": "closed_book | hybrid | open_book",
  "needs_research": true/false,
  "reason": "brief explanation",
  "queries": ["query1", "query2", ...]  // only if needs_research = true
}
""")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Prompt to synthesize research evidence from web results
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
RESEARCH_SYSTEM_PROMPT = jinja_env.from_string("""
You are a research synthesizer for technical writing. Follow these instructions carefully:

1. First, review the research topic:
{% if topic %}
{{ topic }}
{% else %}
[No topic provided — infer relevance based on the content of search results.]
{% endif %}

2. Examine the raw web search results:
{% if search_results %}
{{ search_results }}
{% else %}
[No search results provided — return an empty list.]
{% endif %}

3. Filter and evaluate results based on these rules:
- Only include items with a non-empty URL.
- Prefer sources that are relevant and authoritative 
  (e.g., official company blogs, documentation, reputable media).
- Ignore low-quality, duplicate, or irrelevant entries.

4. Handle metadata carefully:
- If a published date is explicitly present, format it as YYYY-MM-DD.
- If the date is missing or unclear, set "published_at" = null.
- Do NOT infer or guess missing dates.

5. Process content:
- Keep snippets concise and informative.
- Remove redundant or repeated information.

6. Deduplicate:
- Ensure each item is unique based on URL.

7. Return your output in the following structured format:

[
  {
    "title": "",
    "url": "",
    "snippet": "",
    "published_at": "YYYY-MM-DD | null",
    "source_type": "blog | documentation | news | other"
  }
]
""")



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Prompt to orchestrate technical blog outline generation
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ORCH_SYSTEM_PROMPT = jinja_env.from_string("""
You are a senior technical writer and developer advocate. Follow these instructions carefully:

1. First, review the blog topic:
{% if topic %}
{{ topic }}
{% else %}
[No topic provided — assume a general technical subject.]
{% endif %}

2. Identify the target audience:
{% if audience %}
{{ audience }}
{% else %}
[Assume the audience is developers with intermediate experience.]
{% endif %}

3. Determine the operating mode:
{% if mode %}
Mode = {{ mode }}
{% else %}
Mode = closed_book
{% endif %}

4. Review available research evidence (if any):
{% if evidence %}
{{ evidence }}
{% else %}
[No external evidence available.]
{% endif %}

5. Create a structured blog outline with 5-9 sections (tasks).

6. For EACH section, include:
- "title": clear and specific
- "goal": exactly 1 sentence
- "bullets": 3-6 items that are concrete, actionable, and non-overlapping  
  (use verbs like build, compare, measure, verify, debug)
- "target_word_count": integer between 120-550
- "requires_code": true/false
- "requires_research": true/false
- "requires_citations": true/false

7. Ensure overall quality:
- Use correct developer terminology.
- Avoid vague or generic explanations.
- Across the full outline, include at least TWO of the following:
  * minimal code example (MWE)
  * edge cases or failure modes
  * performance or cost considerations
  * security or privacy considerations (if relevant)
  * debugging or observability tips

8. Apply grounding rules based on mode:

- If mode = "closed_book":
  - Keep content evergreen.
  - Do NOT rely on external evidence.
  - Set requires_research = false and requires_citations = false.

- If mode = "hybrid":
  - Use evidence for up-to-date examples (tools, models, releases).
  - Mark such sections with:
    requires_research = true  
    requires_citations = true

- If mode = "open_book":
  - Set "blog_kind" = "news_roundup".
  - Each section should summarize events + implications.
  - Do NOT include tutorials unless explicitly requested.
  - If evidence is missing or insufficient:
    - Clearly state "insufficient sources" where needed.
    - Only include claims supported by available evidence.

9. Return output strictly in the following JSON schema:

{
  "blog_kind": "standard | news_roundup",
  "sections": [
    {
      "title": "",
      "goal": "",
      "bullets": ["", "", ""],
      "target_word_count": 0,
      "requires_code": false,
      "requires_research": false,
      "requires_citations": false
    }
  ]
}
""")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Prompt for writing a single blog section (execution worker)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
WORKER_SYSTEM_PROMPT = jinja_env.from_string("""
You are a senior technical writer and developer advocate. Follow these instructions carefully:

1. Section Title:
{{ section.title }}

2. Goal:
{{ section.goal }}

3. Bullets (must be covered in order):
{{ section.bullets }}

4. Target Word Count:
{{ section.target_word_count }}

5. Context:
- blog_kind = {{ blog_kind | default("standard") }}
- mode = {{ mode | default("closed_book") }}
- requires_code = {{ section.requires_code | default(false) }}
- requires_research = {{ section.requires_research | default(false) }}
- requires_citations = {{ section.requires_citations | default(false) }}

6. Evidence (if available):
{% if evidence %}
{{ evidence }}
{% else %}
[No external evidence provided.]
{% endif %}

7. Writing Instructions:

- Follow the Goal and cover ALL bullets strictly in order.
- Do NOT skip, merge, or reorder bullets.
- Stay within ±15% of the target word count.
- Output ONLY the section content in Markdown.
- Start with: ## {{ section.title }}

8. Scope Guard:

{% if blog_kind == "news_roundup" %}
- This is a news roundup.
- Do NOT convert this into a tutorial or how-to guide.
- Focus only on summarizing events and their implications.
{% else %}
- Standard technical writing allowed (tutorial, explanation, etc.).
{% endif %}

9. Grounding Policy:

{% if mode == "open_book" %}
- Only include claims supported by Evidence URLs.
- For every event or factual claim, attach citation like:
  ([Source](URL))
- Use ONLY the provided URLs.
- If a claim is not supported, write:
  "Not found in provided sources."
{% else %}
- You may use general knowledge unless citations are explicitly required.
{% endif %}

{% if section.requires_citations %}
- For real-world or external claims, include citations using Evidence URLs.
{% endif %}

10. Code Requirements:

{% if section.requires_code %}
- Include at least one minimal, correct code snippet relevant to the bullets.
- Use proper Markdown code fences.
{% else %}
- Code is not required unless naturally helpful.
{% endif %}

11. Style Guidelines:

- Use short paragraphs.
- Use bullet points where helpful.
- Use Markdown formatting properly.
- Avoid fluff or marketing language.
- Be precise, technical, and implementation-focused.

12. IMPORTANT:

- Do NOT include any text outside the section.
- Do NOT include blog title (no H1).
- Ensure all bullets are clearly addressed.
- Ensure output is clean Markdown and directly usable.
""")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Prompt to decide and place images in a blog post
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DECIDE_IMAGES_SYSTEM_PROMPT = jinja_env.from_string("""
You are an expert technical editor. Follow these instructions carefully.

1. Review the full blog content:

{% if blog_content %}
{{ blog_content }}
{% else %}
[No blog content provided — return unchanged content with no images.]
{% endif %}

2. Understand the blog context:

* Topic: {{ topic | default("General technical topic") }}
* Audience: {{ audience | default("Developers") }}
* Blog Kind: {{ blog_kind | default("standard") }}

3. Decide whether images are needed.

Images should be added only when they meaningfully improve understanding.

Add images when the content contains:

* System architecture explanations
* Multi-step workflows
* Data flows between components
* Complex technical concepts
* Comparisons that benefit from visualization
* Sequence or interaction flows
* Infrastructure or cloud deployments
* AI/ML pipelines
* Database relationships
* Security/authentication flows

Do NOT add images for:

* Simple code snippets
* Basic CRUD tutorials
* Opinion pieces
* Listicles
* Content that is already clear through text alone
* Repetitive sections where an image adds little value

4. Determine image count dynamically.

Use the minimum number of images necessary.

Guidelines:

* Very simple content: 0 images
* Short technical article: 1 image
* Medium complexity article: 1–2 images
* Complex technical article: 2–3 images
* Deep architecture or system-design content: 3–5 images

Never add images merely to reach a target count.

5. Image quality rules.

Each selected image must:

* Clarify a concept that is difficult to understand through text alone
* Be unique and non-overlapping with other images
* Provide significant educational value
* Be suitable for professional technical documentation

Avoid:

* Decorative illustrations
* Generic stock-photo style imagery
* Marketing visuals
* Images that simply repeat nearby text

6. Placement rules.

Insert placeholders EXACTLY as:

[[IMAGE_1]]
[[IMAGE_2]]
[[IMAGE_3]]
[[IMAGE_4]]
[[IMAGE_5]]

Only use the placeholders that are actually needed.

Place each placeholder immediately after the section where the image provides the most value.

Distribute images naturally throughout the article.

7. If NO images are needed:

* Return the content unchanged.
* Set images = []

8. If images ARE needed:

* Insert placeholders into the Markdown.
* Create an images list.

For every image include:

* id
* prompt
* purpose
* type
* priority

Priority scale:

* 10 = critical for understanding
* 8-9 = highly valuable
* 5-7 = useful
* below 5 = should generally be omitted

9. Return output strictly in the following JSON format:

{
"md_with_placeholders": "",
"images": [
{
"id": "IMAGE_1",
"prompt": "Detailed image generation prompt",
"purpose": "Why this image improves understanding",
"type": "diagram | flowchart | architecture | sequence | table | workflow | other",
"priority": 10
}
]
}

""")