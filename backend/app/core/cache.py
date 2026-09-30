from fastapi import Response


def set_public_cache(response: Response, *, s_maxage: int = 60, swr: int = 600) -> None:
    """Edge (Cloudflare) may cache; browsers always revalidate against the edge."""
    response.headers["Cache-Control"] = (
        f"public, max-age=0, s-maxage={s_maxage}, stale-while-revalidate={swr}"
    )


def set_no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"