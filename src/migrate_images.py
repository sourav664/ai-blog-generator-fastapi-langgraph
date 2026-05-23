import asyncio
import os
import mimetypes
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from schemas.models import BlogImage, GeneratedBlog
from database.database import get_db, AsyncSessionLocal

async def migrate_images():
    images_dir = Path("images")
    if not images_dir.exists():
        print("No images directory found.")
        return

    async with AsyncSessionLocal() as session:
        # Get all generated blogs to try to match images
        result = await session.execute(select(GeneratedBlog))
        blogs = result.scalars().all()
        
        blog_image_map = {}
        for blog in blogs:
            for img in blog.parsed_images:
                blog_image_map[img] = blog.blog_id

        count = 0
        for file_path in images_dir.iterdir():
            if not file_path.is_file():
                continue
                
            filename = file_path.name
            
            # Check if it's already in DB
            existing_result = await session.execute(select(BlogImage).where(BlogImage.filename == filename))
            if existing_result.scalars().first():
                print(f"Image {filename} already in DB.")
                continue

            # Guess mime type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

            # Try to associate
            blog_id = blog_image_map.get(filename)

            try:
                data = file_path.read_bytes()
                new_image = BlogImage(
                    blog_id=blog_id,
                    filename=filename,
                    data=data,
                    content_type=mime_type
                )
                session.add(new_image)
                count += 1
                print(f"Migrated {filename} (blog_id={blog_id})")
            except Exception as e:
                print(f"Failed to read/migrate {filename}: {e}")

        await session.commit()
        print(f"Successfully migrated {count} images.")

if __name__ == "__main__":
    asyncio.run(migrate_images())
