import os
import sys
import re
import base64
from datetime import datetime
from typing import Optional
from jinja2 import Template
from pathlib import Path




root_dir = Path(__file__).parent.parent


from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage

from langchain_core.messages import get_buffer_string


from utils.model_loader import ModelLoader
from prompt_library.prompt_locator import DECIDE_IMAGES_SYSTEM_PROMPT

from schemas.models import State, GlobalImagePlan, ImagePlacementPlan, ImagePlacementDecision
from logger import GLOBAL_LOGGER
from exception.custom_exception import BlogGeneratorException



class MergeImagesWorker:
    def __init__(self, llm, image_llm):
        self.llm = llm
        self.image_llm = image_llm
        self.memory_saver = MemorySaver()
        self.image_provider = os.getenv("IMAGE_PROVIDER", "openai-image")
        self.logger = GLOBAL_LOGGER.bind(module="MergeImagesWorker")
        
        
    def _merge_content(self, state: State) -> dict:
        try:
            self.logger.info("Sections after workers", sections=state.get("sections"))

            plan = state["plan"]
            sections = state.get("sections", [])

            if not sections:
                self.logger.error("No sections received from workers")
                return {
                    "merged_md": f"# {plan.blog_title}\n\nNo content generated."
                }
            body = "\n\n".join([md for _, md in sorted(sections, key=lambda x: x[0])]).strip()
            merged_md = f"# {plan.blog_title}\n\n{body}\n"

            # Strip any external image links hallucinated by workers
            merged_md = re.sub(r'!\[[^\]]*\]\(https?://[^)]+\)', '', merged_md)
            merged_md = re.sub(r'\n{3,}', '\n\n', merged_md)

            self.logger.info("Merged content successfully")
            return {"merged_md": merged_md}
        except Exception as e:
            self.logger.error("Error merging content", error=str(e))
            raise BlogGeneratorException("Error merging content")

    def _decide_images(self, state: State) -> dict:
        try:
            self.logger.info("Deciding on images")
            planner = self.llm.with_structured_output(ImagePlacementPlan)
            merged_md = state["merged_md"]
            plan = state["plan"]

            # Send only the heading outline to the LLM (tiny payload).
            # This keeps prompt+response tokens well within the model limit
            # regardless of how long the blog is.
            heading_lines = [
                line.strip()
                for line in merged_md.splitlines()
                if line.strip().startswith("## ") or line.strip().startswith("### ")
            ]
            outline = "\n".join(f"{i+1}. {h}" for i, h in enumerate(heading_lines))

            image_plan: ImagePlacementPlan = planner.invoke(
                [
                    SystemMessage(content=str(DECIDE_IMAGES_SYSTEM_PROMPT)),
                    HumanMessage(
                        content=(
                            f"Blog kind: {plan.blog_kind}\n"
                            f"Topic: {state['topic']}\n\n"
                            "Blog section outline (headings only):\n"
                            f"{outline}\n\n"
                            "Decide which sections need an image and return placement decisions."
                        )
                    ),
                ]
            )

            # Python-side placeholder insertion.
            # Find the heading in merged_md and insert the placeholder tag
            # at the end of that section (before the next heading or EOF).
            md_lines = merged_md.splitlines(keepends=True)
            image_specs = []

            for decision in image_plan.images:
                target_heading = decision.after_heading.strip()
                placeholder_tag = f"[[{decision.placeholder}]]"

                # Fuzzy match: strip the leading ## / ### for comparison
                def _heading_text(line: str) -> str:
                    return line.strip().lstrip("#").strip()

                target_text = _heading_text(target_heading)

                insert_after = -1
                for idx, line in enumerate(md_lines):
                    stripped = line.strip()
                    if not (stripped.startswith("## ") or stripped.startswith("### ")):
                        continue
                    # Exact match first
                    if stripped == target_heading:
                        match_idx = idx
                    # Fallback: compare without the ## prefix
                    elif _heading_text(stripped) == target_text:
                        match_idx = idx
                    else:
                        continue

                    # Scan forward to the end of this section
                    for end_idx in range(match_idx + 1, len(md_lines)):
                        next_line = md_lines[end_idx].strip()
                        if next_line.startswith("## ") or next_line.startswith("### "):
                            insert_after = end_idx
                            break
                    else:
                        insert_after = len(md_lines)  # end of file
                    break

                if insert_after == -1:
                    # Heading not found — append at end as fallback
                    self.logger.warning(
                        "after_heading not found in markdown, appending at end",
                        after_heading=target_heading,
                    )
                    insert_after = len(md_lines)

                md_lines.insert(insert_after, f"\n{placeholder_tag}\n")

                image_specs.append({
                    "placeholder": placeholder_tag,
                    "filename": decision.filename,
                    "alt": decision.alt,
                    "caption": decision.caption,
                    "prompt": decision.prompt,
                })

            md_with_placeholders = "".join(md_lines)

            self.logger.info(
                "Decided on images successfully",
                image_count=len(image_specs),
            )
            return {
                "md_with_placeholders": md_with_placeholders,
                "image_specs": image_specs,
            }

        except Exception as e:
            self.logger.error("Error deciding on images", error=str(e))
            raise BlogGeneratorException("Error deciding on images")
    def _generate_image_bytes(self, prompt: str) -> bytes:
        """
        Returns raw image bytes generated 
        
        """
        
        if self.image_provider == "openai-image":
            try:
                self.logger.info("Generating image bytes")
                image_model = self.image_llm(prompt)
                self.logger.info("Generated image successfully")
                
            except Exception as e:
                self.logger.error("Image generation failed", error=str(e))
                raise BlogGeneratorException("Image generation failed")
            
            if not image_model or not getattr(image_model, "data", None):
                raise BlogGeneratorException("No image data returned from OpenAI.")
            
            try:
                image_base64 = image_model.data[0].b64_json
            except Exception:
                raise BlogGeneratorException("Invalid response format: missing base64 image.")
            
            if not image_base64:
                raise BlogGeneratorException("Empty image data received.")
            
            # Decode base64 → bytes
            try:
                image_bytes = base64.b64decode(image_base64)
            except Exception as e:
                raise BlogGeneratorException(f"Failed to decode image: {e}")
            
            self.logger.info("Generated image bytes successfully")
            return image_bytes
        
                
        else:
            try:
               self.logger.info("Generating image bytes")
               image_model = self.image_llm(prompt)
        
            except Exception as e:
                self.logger.error("Image generation failed", error=str(e))
                raise BlogGeneratorException("Image generation failed")
        
        
      
             # Depending on SDK version, parts may hang off resp.candidates[0].content.parts
            parts = getattr(image_model, "parts", None)
            if not parts and getattr(image_model, "candidates", None):
                try:
                    parts = image_model.candidates[0].content.parts
                except Exception:
                    parts = None

            if not parts:
                raise RuntimeError("No image content returned (safety/quota/SDK change).")

            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None):
                    return inline.data

            raise RuntimeError("No inline image bytes found in response.")

    
    
    def _generate_and_place_images(self, state: State) -> dict:
        try:
            self.logger.info("Generating and placing images")
            plan = state["plan"]
            assert plan is not None
            md = state.get("md_with_placeholders") or state["merged_md"]
            image_specs = state.get("image_specs", []) or []
            try:

             
                # If no images requested, just write merged markdown
                if not image_specs:
                    filename = f"{plan.blog_title}.md"
                    blog_path = root_dir / "generated_blogs"
                    blog_path.mkdir(parents=True, exist_ok=True)
                    (blog_path / filename).write_text(md, encoding="utf-8")
                    return {"final": md}
                
            except Exception as e:
                self.logger.error("Error generating blog without images", error=str(e))
                raise BlogGeneratorException("Error generating blog without images")
                
            
            
            images_dir = root_dir / "images"
            images_dir.mkdir(exist_ok=True)

            for spec in image_specs:
                placeholder = spec["placeholder"]
                filename = spec["filename"]
                out_path = images_dir / filename

                # generate only if needed
                if not out_path.exists():
                    try:
                        self.logger.info(f"Generating image for {spec['prompt']}")
                        img_bytes = self._generate_image_bytes(spec["prompt"])
                        out_path.write_bytes(img_bytes)
                    except Exception as e:
                        # graceful fallback: keep doc usable
                        prompt_block = (
                            f"> **[IMAGE GENERATION FAILED]** {spec.get('caption','')}\n>\n"
                            f"> **Alt:** {spec.get('alt','')}\n>\n"
                            f"> **Prompt:** {spec.get('prompt','')}\n>\n"
                            f"> **Error:** {e}\n"
                        )
                        p_clean = placeholder.replace("[", "").replace("]", "").strip()
                        md = re.sub(rf"\[\[?\s*{re.escape(p_clean)}\s*\]\]?", prompt_block, md, flags=re.IGNORECASE)
                        md = md.replace(placeholder, prompt_block) # fallback
                        
                        self.logger.error(
                            f"Error generating image for {spec['prompt']}",
                            error=str(e),
                        )
                        continue
                       

                img_md = f"![{spec['alt']}](/images/{filename})\n*{spec['caption']}*"
                p_clean = placeholder.replace("[", "").replace("]", "").strip()
                md = re.sub(rf"\[\[?\s*{re.escape(p_clean)}\s*\]\]?", img_md, md, flags=re.IGNORECASE)
                md = md.replace(placeholder, img_md) # fallback

            blog_path = root_dir / "generated_blogs"
            blog_path.mkdir(parents=True, exist_ok=True)
            
            safe_title = re.sub(r'[\\/*?:"<>|]', " -", plan.blog_title)
            safe_title = re.sub(r'\s+', ' ', safe_title).strip()
            filename = f"{safe_title}.md"
            blog_path_file = blog_path / filename
            blog_path_file.write_text(md, encoding="utf-8")
            return {"final": md}

            
        except Exception as e:
            self.logger.error("Error generating and placing images", error=str(e))
            raise BlogGeneratorException("Error generating and placing images")
        
        
    def build(self):
        """
        Construct and compile the LangGraph Image Workflow
        """
        
        try:
            self.logger.info("Building LangGraph Image Workflow")
            reducer_graph = StateGraph(State)
            reducer_graph.add_node("merge_content", self._merge_content)
            reducer_graph.add_node("decide_images", self._decide_images)
            reducer_graph.add_node("generate_and_place_images", self._generate_and_place_images)
            reducer_graph.add_edge(START, "merge_content")
            reducer_graph.add_edge("merge_content", "decide_images")
            reducer_graph.add_edge("decide_images", "generate_and_place_images")
            reducer_graph.add_edge("generate_and_place_images", END)
            reducer_subgraph = reducer_graph.compile(checkpointer=self.memory_saver)
            self.logger.info("LangGraph Image Workflow built successfully")

            return reducer_subgraph

        except Exception as e:
            self.logger.error("Error building LangGraph Image Workflow", error=str(e))
            raise BlogGeneratorException("Error building LangGraph Image Workflow")