from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

locks_acquire_total = Counter("locks_acquire_total", "Total acquire attempts", ["mode", "result"])
queue_enqueued_total = Counter("queue_enqueued_total", "Total enqueued messages", ["topic"])
queue_consume_latency = Histogram("queue_consume_latency_seconds", "Consume latency seconds", ["topic"])
cache_invalidation_total = Counter("cache_invalidation_total", "Total cache invalidations", ["reason"])

# ✅ async + set header manual (hindari charset error)
async def metrics_app_handler(request):
    from aiohttp import web
    try:
        data = generate_latest()  # bytes
        return web.Response(body=data, headers={"Content-Type": CONTENT_TYPE_LATEST})
    except Exception as e:
        return web.Response(
            status=200,
            text=f"# metrics_error {type(e).__name__}: {e}\n",
            content_type="text/plain"
        )
# ✅ sync + set header manual (hindari charset error)
# def metrics_wsgi_app(environ, start_response):
#     try:
#         data = generate_latest()  # bytes
#         status = "200 OK"
#         headers = [("Content-Type", CONTENT_TYPE_LATEST)]
#         start_response(status, headers)
#         return [data]
#     except Exception as e:
#         status = "200 OK"
#         headers = [("Content-Type", "text/plain")]
#         start_response(status, headers)
#         error_message = f"# metrics_error {type(e).__name__}: {e}\n"
#         return [error_message.encode("utf-8")]      