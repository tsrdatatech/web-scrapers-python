"""
Request routing and handling for the Crawlee crawler.
"""

from crawlee.router import Router

from src.core.logger import logger
from src.core.parser_manager import ParserManager
from src.core.parser_registry import ParserRegistry


def build_router(registry: ParserRegistry, manager: ParserManager) -> Router:
    """
    Build and configure the request router for Crawlee.

    Args:
        registry: Parser registry instance
        manager: Parser manager instance

    Returns:
        Configured Router instance
    """
    router = Router()

    @router.default_handler
    async def default_handler(context) -> None:
        """Default handler: enqueue links from start URLs using provided selector."""
        request = context.request
        page = context.page
        enqueue_links = context.enqueue_links
        log = context.log

        # Note: Fingerprinting is handled automatically by Crawlee when fingerprint_generator is set

        selector = request.label

        if not selector:
            log.warning(
                f"No selector provided for {request.url} - skipping link discovery"
            )
            return

        log.info(f"Discovering links from {request.url} using selector: {selector}")

        try:
            await enqueue_links(
                selector=selector,
                label="PARSE",
                transform_request_function=lambda req: {
                    **req,
                    "user_data": {
                        "parser": (
                            request.user_data.get("parser")
                            if request.user_data
                            else None
                        )
                    },
                },
            )
        except Exception as e:
            log.error(f"Failed to enqueue links from {request.url}: {e}")

    @router.handler("PARSE")
    async def parse_handler(context) -> None:
        """Parse handler: extract content using appropriate parser."""
        request = context.request
        page = context.page
        log = context.log

        # Note: Fingerprinting is handled automatically by Crawlee when fingerprint_generator is set

        # Select appropriate parser
        forced_parser_id = (
            request.user_data.get("parser") if request.user_data else None
        )
        parser = await manager.select_parser(
            url=request.url,
            forced_id=forced_parser_id,
            context={"request": request, "page": page, "log": log},
        )

        if not parser:
            log.debug(f"No parser available for {request.url}")
            return

        try:
            # Parse the page
            result = await parser.parse(
                page, {"request": request, "page": page, "log": log, "parser": parser}
            )

            if result:
                # Log successful parsing with structured data
                data_logger = logger.bind(
                    event="parsed", parser=parser.id, url=request.url
                )
                data_logger.info(
                    "Successfully parsed content", extra={"data": result.dict()}
                )
            else:
                log.warning(f"Parser {parser.id} returned no data for {request.url}")

        except Exception as e:
            log.error(f"Parser {parser.id} failed for {request.url}: {e}")

    return router
