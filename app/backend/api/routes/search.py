from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from app.backend.api.dependencies import check_rate_limit
from app.backend.schemas.search import SearchResponse, SearchResult
from app.backend.services.search_service import search_all_stores

router = APIRouter()


@router.get("/search", response_model=SearchResponse, dependencies=[Depends(check_rate_limit)])
async def search_products(q: str = Query(min_length=2, max_length=200)):
    products, errors = await search_all_stores(q)
    return SearchResponse(
        query=q,
        total_results=len(products),
        results=[
            SearchResult(
                product_name=p.product_name,
                price=p.price,
                product_url=p.product_url,
                store_slug=p.store_slug,
                store_name=p.store_name,
                image_url=p.image_url,
                in_stock=p.in_stock,
            )
            for p in products
        ],
        errors=errors,
        searched_at=datetime.now(timezone.utc),
    )
