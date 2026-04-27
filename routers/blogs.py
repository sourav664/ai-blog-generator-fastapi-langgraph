import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from schemas import models
from auth import CurrentUser
from config import settings
from database import get_db
from schemas import BlogGenerateRequest, GeneratedBlogResponse, PaginatedBlogsResponse
from schemas.models import GeneratedBlog

# This is an async wrapper for the synchronous langgraph run
from fastapi.concurrency import run_in_threadpool
from workflows.blog_generator_workflow import generate_blog

router = APIRouter()

@router.post("/generate", response_model=GeneratedBlogResponse, status_code=status.HTTP_201_CREATED)
async def generate_blog_endpoint(
    request: BlogGenerateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        # Run the heavy langgraph workflow in a threadpool so we don't block the async event loop
        result = await run_in_threadpool(generate_blog, request.topic)
        
        final_md = result.get("final", "")
        image_specs = result.get("image_specs", [])
        plan = result.get("plan", None)
        
        title = "Generated Blog"
        if plan and hasattr(plan, "blog_title"):
            title = plan.blog_title
        elif plan and isinstance(plan, dict) and "blog_title" in plan:
            title = plan["blog_title"]
        else:
            title = request.topic.title()
            
        images_json = json.dumps([spec["filename"] for spec in image_specs] if image_specs else [])
        
        new_blog = models.GeneratedBlog(
            blog_id=str(uuid.uuid4()),
            title=title,
            content=final_md,
            images=images_json,
            user_id=current_user.id,
            is_published=False
        )
        db.add(new_blog)
        await db.commit()
        await db.refresh(new_blog, attribute_names=["author"])
        return new_blog
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{blog_id}/publish", response_model=GeneratedBlogResponse)
async def publish_blog(
    blog_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.GeneratedBlog).where(models.GeneratedBlog.blog_id == blog_id))
    blog = result.scalars().first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    if blog.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to publish this blog")
        
    blog.is_published = True
    await db.commit()
    await db.refresh(blog, attribute_names=["author"])
    return blog

@router.get("", response_model=PaginatedBlogsResponse)
async def get_my_blogs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = settings.posts_per_page,
):
    count_result = await db.execute(
        select(func.count()).select_from(models.GeneratedBlog).where(models.GeneratedBlog.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.GeneratedBlog)
        .options(selectinload(models.GeneratedBlog.author))
        .where(models.GeneratedBlog.user_id == current_user.id)
        .order_by(models.GeneratedBlog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    blogs = result.scalars().all()
    has_more = skip + len(blogs) < total

    return PaginatedBlogsResponse(
        blogs=[GeneratedBlogResponse.model_validate(b) for b in blogs],
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )

@router.get("/published", response_model=PaginatedBlogsResponse)
async def get_published_blogs(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = settings.posts_per_page,
):
    count_result = await db.execute(
        select(func.count()).select_from(models.GeneratedBlog).where(models.GeneratedBlog.is_published == True)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.GeneratedBlog)
        .options(selectinload(models.GeneratedBlog.author))
        .where(models.GeneratedBlog.is_published == True)
        .order_by(models.GeneratedBlog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    blogs = result.scalars().all()
    has_more = skip + len(blogs) < total

    return PaginatedBlogsResponse(
        blogs=[GeneratedBlogResponse.model_validate(b) for b in blogs],
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )
