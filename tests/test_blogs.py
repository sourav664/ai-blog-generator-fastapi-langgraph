import pytest
from httpx import AsyncClient
from unittest.mock import patch

from tests.conftest import auth_header, create_test_user, login_user


MOCK_BLOG_RESULT = {
    "final": "# AI Blog\n\nThis is generated content.",
    "image_specs": [
        {"filename": "test_image.png"}
    ],
    "plan": {
        "blog_title": "AI Generated Blog"
    }
}


@pytest.mark.anyio
@patch("routers.blogs.generate_blog")
async def test_generate_blog_success(mock_generate_blog, client: AsyncClient):
    mock_generate_blog.return_value = MOCK_BLOG_RESULT

    user = await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.post(
        "/api/blogs/generate",
        json={"topic": "Artificial Intelligence"},
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "AI Generated Blog"
    assert data["content"] == "# AI Blog\n\nThis is generated content."
    assert data["user_id"] == user["id"]
    assert data["is_published"] is False
    assert "blog_id" in data
    assert data["author"]["username"] == "testuser"


@pytest.mark.anyio
async def test_generate_blog_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/blogs/generate",
        json={"topic": "Unauthorized blog"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.anyio
@patch("routers.blogs.generate_blog")
async def test_publish_blog_success(mock_generate_blog, client: AsyncClient):
    mock_generate_blog.return_value = MOCK_BLOG_RESULT

    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.post(
        "/api/blogs/generate",
        json={"topic": "Publishing Blog"},
        headers=headers,
    )

    blog_id = response.json()["blog_id"]

    response = await client.post(
        f"/api/blogs/{blog_id}/publish",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_published"] is True


@pytest.mark.anyio
@patch("routers.blogs.generate_blog")
async def test_publish_blog_wrong_user(mock_generate_blog, client: AsyncClient):
    mock_generate_blog.return_value = MOCK_BLOG_RESULT

    await create_test_user(client, username="user1", email="user1@example.com")
    token1 = await login_user(client, email="user1@example.com")

    response = await client.post(
        "/api/blogs/generate",
        json={"topic": "Private Blog"},
        headers=auth_header(token1),
    )

    blog_id = response.json()["blog_id"]

    await create_test_user(client, username="user2", email="user2@example.com")
    token2 = await login_user(client, email="user2@example.com")

    response = await client.post(
        f"/api/blogs/{blog_id}/publish",
        headers=auth_header(token2),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to publish this blog"


@pytest.mark.anyio
@patch("routers.blogs.generate_blog")
async def test_update_blog_success(mock_generate_blog, client: AsyncClient):
    mock_generate_blog.return_value = MOCK_BLOG_RESULT

    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.post(
        "/api/blogs/generate",
        json={"topic": "Original Blog"},
        headers=headers,
    )

    blog_id = response.json()["blog_id"]

    response = await client.put(
        f"/api/blogs/{blog_id}",
        json={
            "title": "Updated Blog Title",
            "content": "Updated content"
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated Blog Title"
    assert data["content"] == "Updated content"


@pytest.mark.anyio
@patch("routers.blogs.generate_blog")
async def test_update_blog_wrong_user(mock_generate_blog, client: AsyncClient):
    mock_generate_blog.return_value = MOCK_BLOG_RESULT

    await create_test_user(client, username="user1", email="user1@example.com")
    token1 = await login_user(client, email="user1@example.com")

    response = await client.post(
        "/api/blogs/generate",
        json={"topic": "User1 Blog"},
        headers=auth_header(token1),
    )

    blog_id = response.json()["blog_id"]

    await create_test_user(client, username="user2", email="user2@example.com")
    token2 = await login_user(client, email="user2@example.com")

    response = await client.put(
        f"/api/blogs/{blog_id}",
        json={
            "title": "Hacked Blog"
        },
        headers=auth_header(token2),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this blog"


@pytest.mark.anyio
@patch("routers.blogs.generate_blog")
async def test_delete_blog_success(mock_generate_blog, client: AsyncClient):
    mock_generate_blog.return_value = MOCK_BLOG_RESULT

    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.post(
        "/api/blogs/generate",
        json={"topic": "Delete Me"},
        headers=headers,
    )

    blog_id = response.json()["blog_id"]

    response = await client.delete(
        f"/api/blogs/{blog_id}",
        headers=headers,
    )

    assert response.status_code == 204


@pytest.mark.anyio
@patch("routers.blogs.generate_blog")
async def test_get_my_blogs(mock_generate_blog, client: AsyncClient):
    mock_generate_blog.return_value = MOCK_BLOG_RESULT

    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    for i in range(3):
        response = await client.post(
            "/api/blogs/generate",
            json={"topic": f"Blog {i}"},
            headers=headers,
        )

        assert response.status_code == 201

    response = await client.get(
        "/api/blogs",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["blogs"]) == 3
    assert data["has_more"] is False


@pytest.mark.anyio
@patch("routers.blogs.generate_blog")
async def test_get_published_blogs(mock_generate_blog, client: AsyncClient):
    mock_generate_blog.return_value = MOCK_BLOG_RESULT

    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.post(
        "/api/blogs/generate",
        json={"topic": "Public Blog"},
        headers=headers,
    )

    blog_id = response.json()["blog_id"]

    response = await client.post(
        f"/api/blogs/{blog_id}/publish",
        headers=headers,
    )

    assert response.status_code == 200

    response = await client.get("/api/blogs/published")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert data["blogs"][0]["is_published"] is True