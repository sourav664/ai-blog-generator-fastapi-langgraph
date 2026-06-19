import json
import uuid
import mimetypes
from pathlib import Path
from typing import Annotated


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from schemas import models
from src.auth import CurrentUser
from config import settings
from database import get_db, AsyncSessionLocal, get_session_maker
from schemas import BlogGenerateRequest, GeneratedBlogResponse, PaginatedBlogsResponse, BlogUpdateRequest
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
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)],
):
    try:
        # 1. Capture user ID and rollback/end the current transaction before starting the long-running task
        user_id = current_user.id
        await db.rollback()
        await db.close()  # Close the session to release the DB connection to the pool during the long LLM generation

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
            
        # 2. Generate blog_uuid early so we can use it to make image filenames
        #    globally unique. The AI workflow produces predictable names like
        #    "cnn_architecture.png" that collide across blogs on similar topics,
        #    violating the UNIQUE constraint on blog_images.filename.
        blog_uuid = str(uuid.uuid4())
        short_id = blog_uuid.replace("-", "")[:8]   # e.g. "89188bd3"

        # 3. PRE-READ IMAGES FROM DISK and assign unique filenames
        images_dir = Path("images")
        prepared_images = []

        for spec in image_specs:
            original_filename = spec.get("filename")
            if not original_filename:
                continue

            file_path = images_dir / original_filename
            if file_path.exists():
                mime_type, _ = mimetypes.guess_type(original_filename)
                if not mime_type:
                    mime_type = "application/octet-stream"

                # Prefix with short_id to guarantee uniqueness across all blogs
                unique_filename = f"{short_id}_{original_filename}"

                image_data = file_path.read_bytes()
                prepared_images.append({
                    "original_filename": original_filename,
                    "filename": unique_filename,       # stored in DB + served via /images/
                    "data": image_data,
                    "content_type": mime_type,
                    "file_path": file_path,
                })

                # Rewrite markdown references to use the unique filename
                final_md = final_md.replace(
                    f"/images/{original_filename}",
                    f"/images/{unique_filename}",
                )

        # Build images JSON from the now-unique filenames
        images_json = json.dumps(
            [img["filename"] for img in prepared_images] if prepared_images else []
        )

        # 4. OPEN DB TRANSACTION AND EXECUTE RAPIDLY
        async with session_maker() as new_db:
            new_blog = models.GeneratedBlog(
                blog_id=blog_uuid,
                title=title,
                content=final_md,       # references unique filenames
                images=images_json,     # lists unique filenames
                user_id=user_id,
                is_published=False
            )
            new_db.add(new_blog)

            # Flush to register parent ID safely
            await new_db.flush()

            # Add pre-read images to session instantly with zero disk lag
            for img in prepared_images:
                new_image = models.BlogImage(
                    blog_id=new_blog.blog_id,
                    filename=img["filename"],   # already globally unique
                    data=img["data"],
                    content_type=img["content_type"]
                )
                new_db.add(new_image)

            await new_db.commit()
            await new_db.refresh(new_blog, attribute_names=["author"])
        
        # 4. CLEAN UP FILES POST-COMMIT
        # If file deletion fails, it won't crash or corrupt your database transaction
        for img in prepared_images:
            try:
                img["file_path"].unlink()
            except Exception as e:
                import logging
                logging.warning(f"Failed to delete {img['file_path']}: {e}")
         
        return new_blog
    except Exception as e:
        
        import traceback
        traceback.print_exc()

        from exception.custom_exception import BlogGeneratorException

        if isinstance(e, BlogGeneratorException):
            raise HTTPException(status_code=500, detail=e.error_message)

        raise HTTPException(
            status_code=500,
            detail="Failed to generate blog."
        )


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

@router.put("/{blog_id}", response_model=GeneratedBlogResponse)
async def update_blog(
    blog_id: str,
    blog_data: BlogUpdateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.GeneratedBlog).where(models.GeneratedBlog.blog_id == blog_id))
    blog = result.scalars().first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    if blog.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this blog")
        
    if blog_data.title is not None:
        blog.title = blog_data.title
    if blog_data.content is not None:
        blog.content = blog_data.content
        
    await db.commit()
    await db.refresh(blog, attribute_names=["author"])
    return blog

@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.GeneratedBlog).where(models.GeneratedBlog.blog_id == blog_id))
    blog = result.scalars().first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    if blog.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this blog")
        
    await db.delete(blog)
    await db.commit()


@router.post("/{blog_id}/like", response_model=GeneratedBlogResponse)
async def like_blog(
    blog_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.GeneratedBlog)
        .options(selectinload(models.GeneratedBlog.author))
        .where(models.GeneratedBlog.blog_id == blog_id)
    )
    blog = result.scalars().first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    blog.likes = (blog.likes or 0) + 1
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
