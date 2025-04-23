FROM public.ecr.aws/sam/build-python3.13:1.132.0-20241211194230

RUN mkdir /asset
RUN pip install uv
COPY . .
RUN rm -rf dist/*
ENV UV_PYTHON_PREFERENCE=only-system
ENV UV_LINK_MODE=copy
ENV UV_FROZEN=true
RUN --mount=type=cache,target=/root/.cache/uv uv run pytest
RUN --mount=type=cache,target=/root/.cache/uv uv build
RUN --mount=type=cache,target=/root/.cache/uv uv pip install --reinstall --compile-bytecode --target /asset dist/*.whl

CMD ["echo", "Build completed"]

#checkov:skip=CKV_DOCKER_2:This is used for build only
#checkov:skip=CKV_DOCKER_3:This is used for build only