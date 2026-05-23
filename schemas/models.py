from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Literal, Optional, TypedDict, Annotated
import operator

from config import settings

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class Task(BaseModel):
    id: int
    title: str

    goal: str = Field(
        ...,
        description="One sentence describing what the reader should be able to do/understand after this section.",
    )
    bullets: List[str] = Field(
        ...,
        min_length=3,
        max_length=6,
        description="3–6 concrete, non-overlapping subpoints to cover in this section.",
    )
    target_words: int = Field(..., description="Target word count for this section (120–550).")

    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False


class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str
    blog_kind: Literal["explainer", "tutorial", "news_roundup", "comparison", "system_design"] = "explainer"
    constraints: List[str] = Field(default_factory=list)
    tasks: List[Task]


class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None  # keep if Tavily provides; DO NOT rely on it
    snippet: Optional[str] = None
    source: Optional[str] = None


class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    queries: List[str] = Field(default_factory=list)


class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)


class ImageSpec(BaseModel):
    placeholder: str = Field(..., description="e.g. [[IMAGE_1]]")
    filename: str = Field(..., description="Save under images/, e.g. qkv_flow.png")
    alt: str
    caption: str
    prompt: str = Field(..., description="Prompt to send to the image model.")
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"


class GlobalImagePlan(BaseModel):
    md_with_placeholders: str
    images: List[ImageSpec] = Field(default_factory=list)



class State(TypedDict):
    topic: str

    # routing / research
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]

    # workers
    sections: Annotated[List[tuple[int, str]], operator.add]  # (task_id, section_md)

    # reducer/image
    merged_md: str
    md_with_placeholders: str
    image_specs: List[dict]

    final: str


# ---------------------------------------------- DATABASE MODELS -------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)   
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None,
    )
    
    
    
    posts: Mapped[list[GeneratedBlog]] = relationship(back_populates="author", cascade="all, delete-orphan")
    reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"https://{settings.s3_bucket_name}.s3.{settings.s3_region}.amazonaws.com/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"


# class Post(Base):
#     __tablename__ = "posts"

#     id: Mapped[int] = mapped_column(primary_key=True)

#     title: Mapped[str]
#     content: Mapped[str]

#     user_id: Mapped[int]

#     created_at: Mapped[datetime]

#     is_ai_generated: Mapped[bool] = mapped_column(default=False)

#     ai_blog_id: Mapped[str | None]

#     is_published: Mapped[bool] = mapped_column(default=True)

#     likes: Mapped[int] = mapped_column(default=0)

#     images: Mapped[str | None]
    
    
    
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    user: Mapped[User] = relationship(back_populates="reset_tokens")

class GeneratedBlog(Base):
    __tablename__ = "generated_blogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    blog_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    images: Mapped[str] = mapped_column(Text, nullable=True) # JSON string of paths
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    is_published: Mapped[bool] = mapped_column(default=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    
    author: Mapped[User] = relationship(foreign_keys=[user_id])
    
    images_rel: Mapped[list["BlogImage"]] = relationship(
    back_populates="blog",
    cascade="all, delete-orphan",
)

    @property
    def content_without_title(self) -> str:
        import re
        return re.sub(r'^#\s+.*$', '', self.content, count=1, flags=re.MULTILINE).strip()

    @property
    def parsed_images(self) -> list[str]:
        import json
        if self.images:
            try:
                return json.loads(self.images)
            except Exception:
                return []
        return []

    @property
    def description(self) -> str:
        import re
        content = self.content
        # Remove title `# ...`
        content = re.sub(r'^#\s+.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        content = content.strip()
        return content[:300] + '...' if len(content) > 300 else content

class BlogImage(Base):
    __tablename__ = "blog_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    blog_id: Mapped[str] = mapped_column(String(50), ForeignKey("generated_blogs.blog_id", ondelete="CASCADE"), index=True, nullable=True)
    filename: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    blog: Mapped["GeneratedBlog"] = relationship(
        back_populates="images_rel"
    )

