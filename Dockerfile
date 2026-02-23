# 基于上游预置模型镜像，覆盖为当前仓库代码
# 目的：避免构建时下载 HuggingFace 模型导致超时

FROM node:22-alpine AS frontend-builder
WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN sed -i "s|outDir: '../backend/static'|outDir: 'dist'|g" vite.config.ts
RUN npm run build

FROM mumujie/mumuainovel:latest
WORKDIR /app

# 覆盖后端代码
COPY backend/ ./

# 复制本地 Skill 目录（写作技能导入依赖）
COPY skills/ ./skills

# 覆盖前端静态产物
COPY --from=frontend-builder /frontend/dist ./static
